import os
import json
import traci

# Project paths
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = os.path.join(PROJECT_DIR, "config", "city.sumocfg")
OUTPUT_DIR = os.path.join(PROJECT_DIR, "output")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "traffic_data.json")


def main():
    sumo_binary = "sumo"

    # Make sure output folder exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Start SUMO through TraCI
    traci.start([
        sumo_binary,
        "-c", CONFIG_FILE,
        "--seed", "42"
    ])

    print("SUMO connected successfully!")

    data = []

    try:
        while traci.simulation.getMinExpectedNumber() > 0:

            # Move simulation forward by 1 second
            traci.simulationStep()

            current_time = traci.simulation.getTime()

            # ---------------------------------
            # VEHICLE DATA
            # ---------------------------------
            vehicle_ids = traci.vehicle.getIDList()

            total_waiting_time = 0
            total_speed = 0
            total_co2 = 0
            queue_length = 0

            for vehicle_id in vehicle_ids:

                # Accumulated waiting time
                total_waiting_time += traci.vehicle.getAccumulatedWaitingTime(
                    vehicle_id
                )

                # Vehicle speed
                total_speed += traci.vehicle.getSpeed(vehicle_id)

                # CO2 emission
                total_co2 += traci.vehicle.getCO2Emission(vehicle_id)

                # Count stopped vehicles as queued vehicles
                if traci.vehicle.getSpeed(vehicle_id) < 0.1:
                    queue_length += 1

            # Average speed
            if vehicle_ids:
                average_speed = total_speed / len(vehicle_ids)
            else:
                average_speed = 0

            # ---------------------------------
            # TRAFFIC LIGHT DATA
            # ---------------------------------
            traffic_lights = traci.trafficlight.getIDList()

            traffic_light_data = {}

            for tls_id in traffic_lights:

                phase = traci.trafficlight.getPhase(tls_id)
                phase_duration = traci.trafficlight.getPhaseDuration(tls_id)
                next_switch = traci.trafficlight.getNextSwitch(tls_id)

                # Calculate elapsed time of current phase
                phase_elapsed = current_time - (
                    next_switch - phase_duration
                )

                traffic_light_data[tls_id] = {
                    "phase": phase,
                    "phase_elapsed": phase_elapsed
                }

            # ---------------------------------
            # STORE DATA FOR THIS STEP
            # ---------------------------------
            step_data = {
                "time": current_time,
                "vehicle_count": len(vehicle_ids),
                "average_speed": average_speed,
                "waiting_time": total_waiting_time,
                "co2_emission": total_co2,
                "queue_length": queue_length,
                "traffic_lights": traffic_light_data
            }

            data.append(step_data)

            # ---------------------------------
            # PRINT EVERY 100 SECONDS
            # ---------------------------------
            if int(current_time) % 100 == 0:
                print(
                    f"Time: {current_time:.0f}s | "
                    f"Vehicles: {len(vehicle_ids)} | "
                    f"Avg Speed: {average_speed:.2f} m/s | "
                    f"Waiting: {total_waiting_time:.2f}s | "
                    f"Queue: {queue_length} | "
                    f"CO2: {total_co2:.2f} mg"
                )

    finally:
        traci.close()

    # ---------------------------------
    # SAVE DATA TO JSON
    # ---------------------------------
    with open(OUTPUT_FILE, "w") as file:
        json.dump(data, file, indent=2)

    print("SUMO simulation finished.")
    print(f"Data saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()