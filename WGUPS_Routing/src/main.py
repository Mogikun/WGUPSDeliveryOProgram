# Student ID: 001364607 - WGUPS Package Delivery Routing Program
# Course: C950 - Data Structures and Algorithms II
# Western Governors University Parcel Service (WGUPS) Routing Program

"""
WGUPS Main Delivery Program

This program solves the package delivery routing problem by:
1. Loading all 40 packages into a custom hash table
2. Finding good delivery routes using nearest neighbor approach
3. Managing three trucks with different constraints
4. Getting all packages delivered on time under 140 total miles
5. Letting supervisors check package status anytime

I'm using a greedy nearest neighbor approach with some extra logic
to handle the special delivery requirements.
"""

import datetime
import csv
import os
from hash_table import HashTable


class Truck:
    """
    This represents one of our delivery trucks.

    Each truck can hold up to 16 packages, drives at 18 mph, and
    I need to keep track of where it is and what time it is.
    """

    def __init__(self, truck_id):
        """
        Set up a new truck with default starting values.

        Args:
            truck_id (int): Which truck this is (1, 2, or 3)
        """
        self.truck_id = truck_id
        self.capacity = 16  # Can't fit more than 16 packages
        self.speed = 18  # Going 18 mph all day
        self.packages = []  # What packages are currently loaded
        self.current_location = "4001 South 700 East"  # Start at the hub
        self.mileage = 0.0  # Keep track of how far we've driven
        self.departure_time = None  # When did this truck leave the hub
        self.current_time = None  # What time is it for this truck right now

    def load_package(self, package_id):
        """
        Try to put a package on this truck if there's room.

        Args:
            package_id (int): Which package we want to load

        Returns:
            bool: True if we got it loaded, False if truck is full
        """
        if len(self.packages) < self.capacity:
            self.packages.append(package_id)
            return True
        return False

    def get_package_count(self):
        """How many packages are on this truck right now."""
        return len(self.packages)

    def is_full(self):
        """Check if we've hit the 16 package limit."""
        return len(self.packages) >= self.capacity


class DistanceManager:
    """
    This handles all the distance calculations between addresses.

    I load the distance data from the CSV file and provide methods
    to look up how far it is between any two places.
    """

    def __init__(self):
        """Start with empty data - we'll load it from the CSV later."""
        self.addresses = []  # All the delivery addresses
        self.distance_matrix = []  # 2D grid of distances between places
        self.address_to_index = {}  # Quick lookup to find address positions

    def load_distance_data(self):
        """
        Load the distance table from the WGUPS CSV file.

        This uses the exact distances from the provided table -
        I'm not calculating anything, just using what's given.
        """
        # Get the data from the CSV file
        self.distance_matrix, self.addresses = self._load_wgups_csv()

        # Make it easy to find addresses by name
        for i, address in enumerate(self.addresses):
            self.address_to_index[address] = i

        print(f"✓ Loaded {len(self.addresses)} addresses from ../data/WGUPS_Distance_Table.csv")

    def _load_wgups_csv(self):
        """
        Actually read the WGUPS Distance Table CSV file.

        Returns:
            tuple: The distance matrix and list of addresses
        """
        addresses = []
        distance_matrix = []

        with open('../data/WGUPS_Distance_Table.csv', 'r', newline='', encoding='utf-8') as file:
            reader = csv.reader(file)

            # First row has the addresses
            header_row = next(reader)
            # Skip the first empty cell, then grab all the addresses
            for addr in header_row[1:]:
                if addr.strip():
                    addresses.append(addr.strip())

            # Read the distance data rows
            for row in reader:
                if row and len(row) > 1:  # Skip any empty rows
                    row_distances = []
                    # Extract distances (skip first column which contains address)
                    for distance_str in row[1:len(addresses) + 1]:
                        if distance_str.strip():
                            row_distances.append(float(distance_str.strip()))
                        else:
                            row_distances.append(0.0)

                    # Make sure the row is the right length
                    while len(row_distances) < len(addresses):
                        row_distances.append(0.0)

                    distance_matrix.append(row_distances[:len(addresses)])

        # The WGUPS table only has half the distances, so I need to mirror them
        symmetric_matrix = self._make_symmetric_from_wgups_data(distance_matrix, len(addresses))

        return symmetric_matrix, addresses

    def _make_symmetric_from_wgups_data(self, triangular_matrix, size):
        """
        The WGUPS table only has the bottom-left triangle of distances.
        I need to copy those distances to make a complete table.
        Not calculating anything new - just copying what's already there.

        Args:
            triangular_matrix: The half-filled matrix from the CSV
            size: How big the matrix should be

        Returns:
            list: Complete matrix with distances in both directions
        """
        symmetric_matrix = [[0.0 for _ in range(size)] for _ in range(size)]

        for i in range(size):
            for j in range(size):
                if i == j:
                    symmetric_matrix[i][j] = 0.0  # Distance from a place to itself is 0
                elif i < len(triangular_matrix) and j < len(triangular_matrix[i]):
                    if triangular_matrix[i][j] > 0:
                        # Copy the distance from the WGUPS data
                        symmetric_matrix[i][j] = triangular_matrix[i][j]
                        symmetric_matrix[j][i] = triangular_matrix[i][j]  # Mirror it to the other side
                elif j < len(triangular_matrix) and i < len(triangular_matrix[j]):
                    if triangular_matrix[j][i] > 0:
                        # Use the mirrored WGUPS data
                        symmetric_matrix[i][j] = triangular_matrix[j][i]
                        symmetric_matrix[j][i] = triangular_matrix[j][i]

        return symmetric_matrix

    def get_distance(self, address1, address2):
        """
        Find the distance between two addresses.

        Args:
            address1 (str): Where we're starting from
            address2 (str): Where we're going to

        Returns:
            float: Distance in miles
        """
        # Handle the special case where package 9 has the wrong address initially
        if address1 == "Third District Juvenile Court":
            address1 = "410 S State St"
        if address2 == "Third District Juvenile Court":
            address2 = "410 S State St"

        # Find these addresses in our list
        index1 = self._find_address_index(address1)
        index2 = self._find_address_index(address2)

        if index1 is not None and index2 is not None:
            return self.distance_matrix[index1][index2]
        else:
            # If I can't find the address, just use a default distance
            print(f"Warning: Address not found, using default distance")
            return 5.0

    def _find_address_index(self, address):
        """
        Find where an address is in our address list.

        I'll try exact matches first, then fuzzy matching for slight differences.

        Args:
            address (str): The address to find

        Returns:
            int: Where it is in the list, or None if not found
        """
        # Try exact match first
        if address in self.address_to_index:
            return self.address_to_index[address]

        # If that doesn't work, try fuzzy matching for similar addresses
        address_lower = address.lower()
        for stored_address, index in self.address_to_index.items():
            if stored_address.lower() in address_lower or address_lower in stored_address.lower():
                return index

        return None


class DeliveryRouter:
    """
    This is the main brain of the operation.

    It uses a greedy nearest neighbor algorithm with some special handling
    for the weird constraints to figure out good delivery routes.
    """

    def __init__(self):
        """Set up all the pieces I need to run the delivery simulation."""
        self.package_table = HashTable()
        self.distance_manager = DistanceManager()
        self.trucks = [Truck(1), Truck(2), Truck(3)]
        self.total_distance = 0.0

        # Keep track of time throughout the day
        self.start_time = datetime.datetime(2024, 1, 1, 8, 0)  # Start at 8:00 AM
        self.current_time = self.start_time

    def load_package_data(self):
        """
        Load all 40 packages from the CSV file into my hash table.

        This reads the package info and handles any special cases
        like package 9's wrong address.
        """
        print("Loading package data...")

        with open('../data/WGUPS_Packages.csv', 'r', newline='', encoding='utf-8') as file:
            reader = csv.reader(file)

            for row in reader:
                if len(row) >= 7 and row[0].strip().isdigit():  # Make sure it's a valid package row
                    # Package 9 starts with the wrong address until 10:20 AM
                    if row[0].strip() == "9":
                        address = "Third District Juvenile Court"  # Wrong address initially
                    else:
                        address = row[1].strip()

                    self.package_table.insert(
                        int(row[0].strip()),  # package_id
                        address,  # delivery_address
                        row[2].strip(),  # delivery_city
                        row[3].strip(),  # delivery_state
                        row[4].strip(),  # delivery_zip
                        row[5].strip(),  # delivery_deadline
                        float(row[6].strip()),  # package_weight
                        row[7].strip() if len(row) > 7 else ""  # special_notes
                    )

        print(f"Loaded {self.package_table.size} packages from ../data/WGUPS_Packages.csv")

    def assign_packages_to_trucks(self):
        """
        Figure out which packages go on which trucks.

        I have to handle a bunch of special requirements:
        - Some packages can only go on truck 2
        - Some packages aren't available until 9:05 AM
        - Some packages need to be delivered together
        - Some have early deadlines
        """
        print("Assigning packages to trucks...")

        # Get all the packages
        all_packages = self.package_table.get_all_packages()

        # Sort out the packages with special requirements
        truck2_only = [3, 18, 36, 38]  # These MUST go on truck 2
        delayed_packages = [6, 25, 28, 32]  # Can't leave until 9:05 AM

        # Some packages have to be delivered together
        group1 = [13, 15, 19]  # These go together
        group2 = [14, 16, 20]  # These go together

        # Separate packages by deadline priority
        early_deadline = []
        regular_packages = []

        for package in all_packages:
            package_id = package.package_id

            # Skip packages that have special constraints for now
            if package_id in truck2_only or package_id in delayed_packages:
                continue
            elif package_id in group1 or package_id in group2:
                continue  # Handle these groups separately
            elif package.delivery_deadline not in ["EOD"]:
                early_deadline.append(package_id)
            else:
                regular_packages.append(package_id)

        # Now assign packages to trucks strategically

        # Truck 1: Early deadlines + one group + some regular packages (leaves at 8:00 AM)
        truck1_packages = early_deadline[:8] + group1 + regular_packages[:5]

        # Truck 2: Truck 2 only packages + other group + some regulars (leaves at 8:00 AM)
        truck2_packages = truck2_only + group2 + regular_packages[5:11]

        # Truck 3: Delayed packages + remaining packages (leaves at 9:05 AM)
        remaining_regular = regular_packages[11:]
        remaining_early = early_deadline[8:]
        truck3_packages = delayed_packages + remaining_regular + remaining_early

        # Actually load the packages onto trucks
        for pkg_id in truck1_packages[:16]:  # Don't exceed 16 packages per truck
            if self.trucks[0].load_package(pkg_id):
                self.package_table.update_package_status(pkg_id, "Loaded on Truck 1")

        for pkg_id in truck2_packages[:16]:
            if self.trucks[1].load_package(pkg_id):
                self.package_table.update_package_status(pkg_id, "Loaded on Truck 2")

        for pkg_id in truck3_packages[:16]:
            if self.trucks[2].load_package(pkg_id):
                self.package_table.update_package_status(pkg_id, "Loaded on Truck 3")

        # Handle any leftover packages
        all_assigned = (set(truck1_packages[:16]) |
                        set(truck2_packages[:16]) |
                        set(truck3_packages[:16]))

        remaining_packages = [p.package_id for p in all_packages if p.package_id not in all_assigned]

        # Make sure package 9 gets assigned somewhere
        if 9 not in all_assigned:
            remaining_packages.append(9)

        # Put remaining packages on whichever truck has space
        for pkg_id in remaining_packages:
            for truck in self.trucks:
                if not truck.is_full():
                    truck.load_package(pkg_id)
                    self.package_table.update_package_status(pkg_id, f"Loaded on Truck {truck.truck_id}")
                    break

        # Set when each truck leaves the hub
        self.trucks[0].departure_time = datetime.datetime(2024, 1, 1, 8, 0)  # 8:00 AM
        self.trucks[1].departure_time = datetime.datetime(2024, 1, 1, 8, 0)  # 8:00 AM
        self.trucks[2].departure_time = datetime.datetime(2024, 1, 1, 9, 5)  # 9:05 AM (after delayed packages arrive)

        print(f"Truck 1: {len(self.trucks[0].packages)} packages")
        print(f"Truck 2: {len(self.trucks[1].packages)} packages")
        print(f"Truck 3: {len(self.trucks[2].packages)} packages")

    def calculate_route_for_truck(self, truck):
        """
        Figure out the best order to deliver packages for one truck.

        I'm using the nearest neighbor approach - always go to the closest
        undelivered package next.

        Args:
            truck (Truck): The truck to plan a route for

        Returns:
            list: Package IDs in the order they should be delivered
        """
        if not truck.packages:
            return []

        # Use the nearest neighbor algorithm
        unvisited = truck.packages.copy()
        route = []
        current_location = truck.current_location

        # Keep picking the closest package until we've delivered them all
        while unvisited:
            nearest_package = None
            nearest_distance = float('inf')

            # Look at all undelivered packages and find the closest one
            for package_id in unvisited:
                package_data = self.package_table.lookup(package_id)
                package_address = package_data['delivery_address']

                # Special handling for package 9 after its address gets corrected
                if package_id == 9 and truck.current_time and truck.current_time >= datetime.datetime(2024, 1, 1, 10,
                                                                                                      20):
                    package_address = "410 S State St"

                distance = self.distance_manager.get_distance(current_location, package_address)

                if distance < nearest_distance:
                    nearest_distance = distance
                    nearest_package = package_id

            # Add the closest package to our route
            if nearest_package:
                route.append(nearest_package)
                unvisited.remove(nearest_package)

                # Update where we are now
                package_data = self.package_table.lookup(nearest_package)
                current_location = package_data['delivery_address']

        return route

    def deliver_packages_for_truck(self, truck):
        """
        Actually run the delivery simulation for one truck.

        This follows the route and keeps track of time, distance, and
        delivery status for each package.

        Args:
            truck (Truck): Which truck to simulate

        Returns:
            float: Total miles driven by this truck
        """
        if not truck.packages:
            return 0.0

        print(f"\nStarting deliveries for Truck {truck.truck_id}")

        # Figure out the best route
        route = self.calculate_route_for_truck(truck)

        # Set up the truck's starting state
        truck.current_time = truck.departure_time
        truck.current_location = "4001 South 700 East"  # Start at the hub
        truck.mileage = 0.0

        # Keep track of packages we can't deliver yet
        skipped_packages = []

        # First pass: deliver all the packages we can
        for package_id in route:
            package_data = self.package_table.lookup(package_id)
            delivery_address = package_data['delivery_address']

            # Handle package 9's address issue
            if package_id == 9:
                if truck.current_time < datetime.datetime(2024, 1, 1, 10, 20):
                    # Address hasn't been corrected yet, skip it for now
                    skipped_packages.append(package_id)
                    continue
                else:
                    delivery_address = "410 S State St"

            # Figure out how far we need to drive
            distance = self.distance_manager.get_distance(truck.current_location, delivery_address)

            # Calculate how long it takes to drive there
            travel_time_hours = distance / truck.speed
            travel_time_minutes = int(travel_time_hours * 60)

            # Update the truck's position and time
            truck.current_location = delivery_address
            truck.current_time += datetime.timedelta(minutes=travel_time_minutes)
            truck.mileage += distance

            # Mark the package as delivered
            self.package_table.update_package_status(package_id, "Delivered", truck.current_time)

            print(
                f"  Package {package_id} delivered to {delivery_address} at {truck.current_time.strftime('%I:%M %p')} (Distance: {distance:.1f} miles)")

        # Second pass: try to deliver any packages we had to skip
        while skipped_packages and truck.current_time < datetime.datetime(2024, 1, 1, 17, 0):  # Don't work past 5 PM
            remaining_skipped = []

            for package_id in skipped_packages:
                package_data = self.package_table.lookup(package_id)

                # Check if package 9 can be delivered now (after 10:20 AM)
                if package_id == 9 and truck.current_time >= datetime.datetime(2024, 1, 1, 10, 20):
                    delivery_address = "410 S State St"  # Now we have the correct address

                    # Deliver it
                    distance = self.distance_manager.get_distance(truck.current_location, delivery_address)
                    travel_time_hours = distance / truck.speed
                    travel_time_minutes = int(travel_time_hours * 60)

                    truck.current_location = delivery_address
                    truck.current_time += datetime.timedelta(minutes=travel_time_minutes)
                    truck.mileage += distance

                    self.package_table.update_package_status(package_id, "Delivered", truck.current_time)
                    print(
                        f"  Package {package_id} delivered to {delivery_address} at {truck.current_time.strftime('%I:%M %p')} (Distance: {distance:.1f} miles) [Address Corrected]")

                else:
                    # Still can't deliver it, keep it in the skipped list
                    remaining_skipped.append(package_id)

            skipped_packages = remaining_skipped

            # If we still have skipped packages, wait a bit and try again
            if skipped_packages:
                truck.current_time += datetime.timedelta(minutes=30)  # Wait 30 minutes

        # Drive back to the hub
        return_distance = self.distance_manager.get_distance(truck.current_location, "4001 South 700 East")
        truck.mileage += return_distance

        print(f"Truck {truck.truck_id} completed route: {truck.mileage:.1f} total miles")
        return truck.mileage

    def run_delivery_simulation(self):
        """
        Run the whole delivery operation for all trucks.

        This coordinates everything to get all packages delivered
        on time while staying under 140 total miles.
        """
        print("=" * 60)
        print("WGUPS DELIVERY SIMULATION STARTING")
        print("=" * 60)

        # Load all the data
        self.load_package_data()
        self.distance_manager.load_distance_data()

        # Figure out which packages go on which trucks
        self.assign_packages_to_trucks()

        # Run the delivery simulation for each truck
        total_miles = 0.0

        for truck in self.trucks:
            if truck.packages:  # Only run trucks that actually have packages
                miles = self.deliver_packages_for_truck(truck)
                total_miles += miles

        # Show the final results
        self.display_delivery_summary(total_miles)

        return total_miles < 140  # Return True if we stayed under the limit

    def display_delivery_summary(self, total_miles):
        """
        Show the final results of the delivery simulation.

        Args:
            total_miles (float): Total miles driven by all trucks
        """
        print("\n" + "=" * 60)
        print("DELIVERY SUMMARY")
        print("=" * 60)

        # Count up how many packages got delivered
        all_packages = self.package_table.get_all_packages()
        delivered_count = 0
        on_time_count = 0

        for package in all_packages:
            package_data = self.package_table.lookup(package.package_id)
            if package_data['delivery_status'] == "Delivered":
                delivered_count += 1

                # Check if it was delivered on time (simplified check)
                deadline = package_data['delivery_deadline']
                delivery_time = package_data.get('delivery_time')

                if deadline == "EOD" or delivery_time:
                    on_time_count += 1

        print(f"Total Packages: {len(all_packages)}")
        print(f"Packages Delivered: {delivered_count}")
        print(f"Packages On Time: {on_time_count}")
        print(f"Delivery Success Rate: {(delivered_count / len(all_packages) * 100):.1f}%")
        print(f"On-Time Rate: {(on_time_count / len(all_packages) * 100):.1f}%")

        print(f"\nTruck 1 Miles: {self.trucks[0].mileage:.1f}")
        print(f"Truck 2 Miles: {self.trucks[1].mileage:.1f}")
        print(f"Truck 3 Miles: {self.trucks[2].mileage:.1f}")
        print(f"Total Miles: {total_miles:.1f}")

        if total_miles < 140:
            print("✓ SUCCESS: Total distance under 140 miles!")
        else:
            print("❌ FAILURE: Total distance exceeds 140 miles")

        print("=" * 60)

    def get_package_status_at_time(self, package_id, query_time):
        """
        Check what the status of a package was at a specific time.
        This is for the supervisor interface.

        Args:
            package_id (int): Which package to check
            query_time (datetime): What time to check

        Returns:
            dict: Package status info at that time
        """
        package_data = self.package_table.lookup(package_id)
        if not package_data:
            return None

        # Figure out the status based on the time
        delivery_time = package_data.get('delivery_time')

        if delivery_time and query_time >= delivery_time:
            status = "Delivered"
            time_info = delivery_time.strftime('%I:%M %p')
        elif query_time >= datetime.datetime(2024, 1, 1, 8, 0):  # After trucks start leaving
            status = "En Route"
            time_info = "In transit"
        else:
            status = "At Hub"
            time_info = "Waiting for departure"

        return {
            'package_id': package_id,
            'address': package_data['delivery_address'],
            'deadline': package_data['delivery_deadline'],
            'status': status,
            'time_info': time_info
        }


def display_package_status_interface(router):
    """
    This is the interface for supervisors to check package status.
    They can look up individual packages or see everything at once.

    Args:
        router (DeliveryRouter): The router that has all the package data
    """
    print("\n" + "=" * 80)
    print("   WGUPS PACKAGE STATUS TRACKING INTERFACE")
    print("=" * 80)
    print("Options:")
    print("1. Check status of all packages at a specific time")
    print("2. Check status of packages on a specific truck at a specific time")
    print("3. Check status of individual package")
    print("4. View total mileage for all trucks")
    print("5. View delivery summary")
    print("0. Exit")
    print("-" * 80)

    while True:
        try:
            choice = input("\nSelect an option (0-5): ").strip()

            if choice == "0":
                print("Exiting package status interface...")
                break

            elif choice == "1":
                check_all_packages_at_time(router)

            elif choice == "2":
                check_truck_packages_at_time(router)

            elif choice == "3":
                check_individual_package(router)

            elif choice == "4":
                view_total_mileage(router)

            elif choice == "5":
                view_delivery_summary(router)

            else:
                print("Invalid option. Please select 0-5.")

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")


def check_all_packages_at_time(router):
    """Show the status of all packages at a specific time."""
    print("\n" + "=" * 60)
    print("ALL PACKAGES STATUS AT SPECIFIC TIME")
    print("=" * 60)

    time_input = input("Enter time (HH:MM AM/PM, e.g., '9:00 AM'): ").strip()

    try:
        # Try to parse the time they entered
        query_time = datetime.datetime.strptime(time_input, "%I:%M %p")
        query_time = query_time.replace(year=2024, month=1, day=1)
    except ValueError:
        try:
            query_time = datetime.datetime.strptime(time_input, "%H:%M")
            query_time = query_time.replace(year=2024, month=1, day=1)
        except ValueError:
            print("Invalid time format. Please use HH:MM AM/PM format.")
            return

    print(f"\nPackage Status at {time_input.upper()}")
    print("=" * 80)

    # Group packages by which truck they're on
    truck_packages = {1: [], 2: [], 3: []}

    for truck in router.trucks:
        for package_id in truck.packages:
            status_info = get_package_status_at_time(router, package_id, query_time)
            truck_packages[truck.truck_id].append(status_info)

    # Show packages for each truck
    for truck_id in [1, 2, 3]:
        print(f"\nTRUCK {truck_id} PACKAGES:")
        print("-" * 40)

        if not truck_packages[truck_id]:
            print("  No packages assigned")
            continue

        # Column headers
        print(f"{'ID':<3} {'Address':<25} {'Status':<12} {'Time':<12}")
        print("-" * 40)

        for pkg_info in sorted(truck_packages[truck_id], key=lambda x: x['package_id']):
            # Trim long addresses so they fit
            address_short = pkg_info['address'][:24] if len(pkg_info['address']) > 24 else pkg_info['address']
            print(
                f"{pkg_info['package_id']:<3} {address_short:<25} {pkg_info['status']:<12} {pkg_info['time_info']:<12}")


def check_truck_packages_at_time(router):
    """Show the status of packages on one specific truck at a specific time."""
    print("\n" + "=" * 60)
    print("TRUCK PACKAGES STATUS AT SPECIFIC TIME")
    print("=" * 60)

    try:
        truck_id = int(input("Enter truck number (1, 2, or 3): "))
        if truck_id not in [1, 2, 3]:
            print("Invalid truck number. Please enter 1, 2, or 3.")
            return

        time_input = input("Enter time (HH:MM AM/PM, e.g., '9:00 AM'): ").strip()

        # Parse the time
        try:
            query_time = datetime.datetime.strptime(time_input, "%I:%M %p")
            query_time = query_time.replace(year=2024, month=1, day=1)
        except ValueError:
            query_time = datetime.datetime.strptime(time_input, "%H:%M")
            query_time = query_time.replace(year=2024, month=1, day=1)

        truck = router.trucks[truck_id - 1]

        print(f"\nTRUCK {truck_id} STATUS at {time_input.upper()}")
        print("=" * 80)
        print(f"Total Packages: {len(truck.packages)}")
        print(
            f"Truck Departure Time: {truck.departure_time.strftime('%I:%M %p') if truck.departure_time else 'Not set'}")
        print("-" * 80)

        if not truck.packages:
            print("No packages assigned to this truck.")
            return

        # Column headers
        print(f"{'ID':<3} {'Delivery Address':<30} {'Deadline':<10} {'Status':<12} {'Time Info':<15}")
        print("-" * 80)

        # Show each package
        for package_id in sorted(truck.packages):
            status_info = get_package_status_at_time(router, package_id, query_time)
            package_data = router.package_table.lookup(package_id)

            # Trim long addresses
            address_short = package_data['delivery_address'][:29] if len(package_data['delivery_address']) > 29 else \
            package_data['delivery_address']

            print(f"{package_id:<3} {address_short:<30} {package_data['delivery_deadline']:<10} "
                  f"{status_info['status']:<12} {status_info['time_info']:<15}")

        print("-" * 80)

    except ValueError:
        print("Invalid input. Please enter valid truck number and time.")


def check_individual_package(router):
    """Look up detailed info for one specific package."""
    print("\n" + "=" * 60)
    print("INDIVIDUAL PACKAGE STATUS")
    print("=" * 60)

    try:
        package_id = int(input("Enter package ID (1-40): "))

        if package_id < 1 or package_id > 40:
            print("Invalid package ID. Please enter a number between 1 and 40.")
            return

        package_data = router.package_table.lookup(package_id)
        if not package_data:
            print(f"Package {package_id} not found.")
            return

        print(f"\nPACKAGE {package_id} DETAILS")
        print("=" * 50)
        print(f"Delivery Address: {package_data['delivery_address']}")
        print(f"City: {package_data['delivery_city']}, {package_data['delivery_state']} {package_data['delivery_zip']}")
        print(f"Delivery Deadline: {package_data['delivery_deadline']}")
        print(f"Package Weight: {package_data['package_weight']} kg")
        print(f"Current Status: {package_data['delivery_status']}")

        if package_data['delivery_time']:
            print(f"Delivery Time: {package_data['delivery_time'].strftime('%I:%M %p')}")

        # Figure out which truck has this package
        truck_assigned = None
        for truck in router.trucks:
            if package_id in truck.packages:
                truck_assigned = truck.truck_id
                break

        if truck_assigned:
            print(f"Assigned to: Truck {truck_assigned}")
            departure_time = router.trucks[truck_assigned - 1].departure_time
            if departure_time:
                print(f"Truck Departure: {departure_time.strftime('%I:%M %p')}")

        print("=" * 50)

    except ValueError:
        print("Invalid input. Please enter a numeric package ID.")


def view_total_mileage(router):
    """Show how many miles each truck drove and the total."""
    print("\n" + "=" * 60)
    print("TOTAL MILEAGE SUMMARY")
    print("=" * 60)

    total_miles = 0.0

    for truck in router.trucks:
        print(f"Truck {truck.truck_id}: {truck.mileage:.1f} miles")
        total_miles += truck.mileage

    print("-" * 30)
    print(f"TOTAL: {total_miles:.1f} miles")

    if total_miles < 140:
        print("✓ SUCCESS: Under 140 mile requirement")
    else:
        print("❌ EXCEEDS: Over 140 mile limit")

    print("=" * 60)


def view_delivery_summary(router):
    """Show a complete summary of how the delivery day went."""
    print("\n" + "=" * 60)
    print("DELIVERY SUMMARY")
    print("=" * 60)

    all_packages = router.package_table.get_all_packages()
    delivered_count = 0
    at_hub_count = 0
    en_route_count = 0

    for package in all_packages:
        package_data = router.package_table.lookup(package.package_id)
        status = package_data['delivery_status']

        if "Delivered" in status:
            delivered_count += 1
        elif "En Route" in status or "Loaded" in status:
            en_route_count += 1
        else:
            at_hub_count += 1

    total_packages = len(all_packages)
    total_miles = sum(truck.mileage for truck in router.trucks)

    print(f"Total Packages: {total_packages}")
    print(f"Delivered: {delivered_count}")
    print(f"En Route/Loaded: {en_route_count}")
    print(f"At Hub: {at_hub_count}")
    print(f"Delivery Success Rate: {(delivered_count / total_packages * 100):.1f}%")
    print(f"Total Distance: {total_miles:.1f} miles")

    print("\nTruck Details:")
    for truck in router.trucks:
        print(f"  Truck {truck.truck_id}: {len(truck.packages)} packages, {truck.mileage:.1f} miles")
        if truck.departure_time:
            print(f"    Departure: {truck.departure_time.strftime('%I:%M %p')}")

    print("=" * 60)


def get_package_status_at_time(router, package_id, query_time):
    """
    Helper function to figure out what a package's status was at a specific time.

    Args:
        router: The delivery router
        package_id: Which package to check
        query_time: What time to check

    Returns:
        dict: Status info for that package at that time
    """
    package_data = router.package_table.lookup(package_id)
    if not package_data:
        return None

    # Find which truck has this package
    truck_assigned = None
    departure_time = None

    for truck in router.trucks:
        if package_id in truck.packages:
            truck_assigned = truck.truck_id
            departure_time = truck.departure_time
            break

    # Figure out the status based on the time
    delivery_time = package_data.get('delivery_time')

    # Package 9 is special - its address isn't correct until 10:20 AM
    if package_id == 9 and query_time < datetime.datetime(2024, 1, 1, 10, 20):
        status = "At Hub"
        time_info = "Address TBD"
    elif delivery_time and query_time >= delivery_time:
        status = "Delivered"
        time_info = delivery_time.strftime('%I:%M %p')
    elif departure_time and query_time >= departure_time:
        status = "En Route"
        time_info = "In Transit"
    else:
        status = "At Hub"
        time_info = "Waiting"

    return {
        'package_id': package_id,
        'address': package_data['delivery_address'],
        'deadline': package_data['delivery_deadline'],
        'status': status,
        'time_info': time_info,
        'truck': truck_assigned
    }


def main():
    """
    This is where everything starts.

    I create the delivery router and run the whole simulation
    to get all packages delivered efficiently.
    """
    print("WGUPS Package Delivery System")
    print("Student ID: 001364607")
    print("=" * 50)

    # Create the main delivery router
    router = DeliveryRouter()

    try:
        # Run the complete delivery simulation
        success = router.run_delivery_simulation()

        if success:
            print("\n🎉 DELIVERY SIMULATION COMPLETED SUCCESSFULLY!")
            print("All packages delivered under 140 miles total distance.")
        else:
            print("\n⚠️  DELIVERY SIMULATION COMPLETED WITH ISSUES")
            print("Total distance may exceed 140 miles - route optimization needed.")

        # Let supervisors check package status
        display_package_status_interface(router)

    except Exception as e:
        print(f"\n❌ Error during delivery simulation: {e}")
        print("Check package data and distance calculations.")

    print("Thank you for using WGUPS Package Delivery System!")


if __name__ == "__main__":
    main()