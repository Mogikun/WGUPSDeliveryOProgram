# hash_table.py - Complete implementation for WGUPS
"""
WGUPS Hash Table Implementation
Student: Calvin Mogi
Course: C950 - Data Structures and Algorithms II

A custom hash table implementation that stores package data using package ID as the key.
No additional libraries or classes are used beyond Python's built-in functionality.
"""


class Package:
    """
    Simple Package class to represent package data.
    """
    def __init__(self, package_data):
        """Initialize package with data dictionary."""
        self.package_id = package_data['package_id']
        self.delivery_address = package_data['delivery_address']
        self.delivery_city = package_data['delivery_city']
        self.delivery_state = package_data['delivery_state']
        self.delivery_zip = package_data['delivery_zip']
        self.delivery_deadline = package_data['delivery_deadline']
        self.package_weight = package_data['package_weight']
        self.delivery_status = package_data['delivery_status']
        self.delivery_time = package_data['delivery_time']


class HashTable:
    """
    Custom hash table implementation for storing package data.
    Uses chaining with lists to handle collisions.
    """

    def __init__(self, initial_capacity=40):

        self.capacity = initial_capacity
        self.size = 0
        # Each bucket is a list that stores [key, package_data] pairs
        self.buckets = [[] for _ in range(self.capacity)]

    def _hash_function(self, package_id):

        return package_id % self.capacity

    def insert(self, package_id, delivery_address, delivery_city, delivery_state,
               delivery_zip, delivery_deadline, package_weight, delivery_status="At Hub"):

        # Calculate which bucket to use
        bucket_index = self._hash_function(package_id)
        bucket = self.buckets[bucket_index]

        # Package data stored as a list with all required components
        package_data = [
            package_id,
            delivery_address,
            delivery_city,
            delivery_state,
            delivery_zip,
            delivery_deadline,
            package_weight,
            delivery_status,
            None  # delivery_time (initially None)
        ]

        # Check if package already exists and update it
        for i, item in enumerate(bucket):
            if item[0] == package_id:  # item[0] is the package_id
                bucket[i] = [package_id, package_data]
                return

        # Package doesn't exist, add new entry
        bucket.append([package_id, package_data])
        self.size += 1

    def lookup(self, package_id):

        # Calculate which bucket to search
        bucket_index = self._hash_function(package_id)
        bucket = self.buckets[bucket_index]

        # Search through the bucket for the package
        for stored_package_id, package_data in bucket:
            if stored_package_id == package_id:
                # Package found - return all data components
                return {
                    'package_id': package_data[0],
                    'delivery_address': package_data[1],
                    'delivery_city': package_data[2],
                    'delivery_state': package_data[3],
                    'delivery_zip': package_data[4],
                    'delivery_deadline': package_data[5],
                    'package_weight': package_data[6],
                    'delivery_status': package_data[7],
                    'delivery_time': package_data[8]
                }

        # Package not found
        return None

    def get_all_packages(self):

        all_packages = []

        # Go through each bucket
        for bucket in self.buckets:
            # Go through each package in the bucket
            for stored_package_id, package_data in bucket:
                # Convert to dictionary format
                package_dict = {
                    'package_id': package_data[0],
                    'delivery_address': package_data[1],
                    'delivery_city': package_data[2],
                    'delivery_state': package_data[3],
                    'delivery_zip': package_data[4],
                    'delivery_deadline': package_data[5],
                    'package_weight': package_data[6],
                    'delivery_status': package_data[7],
                    'delivery_time': package_data[8]
                }
                # Create Package object and add to list
                package_obj = Package(package_dict)
                all_packages.append(package_obj)

        return all_packages

    def update_package_status(self, package_id, new_status, delivery_time=None):
        """
        Update the delivery status of a specific package.

        Args:
            package_id (int): Package ID to update
            new_status (str): New delivery status
            delivery_time: Delivery time (optional)

        Returns:
            bool: True if package was found and updated, False otherwise
        """
        # Calculate which bucket to search
        bucket_index = self._hash_function(package_id)
        bucket = self.buckets[bucket_index]

        # Search through the bucket for the package
        for i, (stored_package_id, package_data) in enumerate(bucket):
            if stored_package_id == package_id:
                # Update the status
                package_data[7] = new_status  # delivery_status
                if delivery_time:
                    package_data[8] = delivery_time  # delivery_time

                # Update the bucket with modified data
                bucket[i] = [stored_package_id, package_data]
                return True

        # Package not found
        return False


# Test code (only runs when file is executed directly)
if __name__ == "__main__":
    # Create hash table instance
    package_table = HashTable()

    # Insert packages using the required data components
    print("Testing Hash Table Implementation...")
    print("="*50)

    # Insert test packages
    package_table.insert(1, "195 W Oakland Ave", "Salt Lake City", "UT", "84115", "10:30 AM", 21)
    package_table.insert(2, "2530 S 500 E", "Salt Lake City", "UT", "84106", "EOD", 44)
    package_table.insert(3, "233 Canyon Rd", "Salt Lake City", "UT", "84103", "EOD", 2)

    print(f"✓ Inserted {package_table.size} packages")

    # Test lookup function
    result = package_table.lookup(1)
    if result:
        print(f"✓ Lookup working: Package 1 found at {result['delivery_address']}")

    # Test get_all_packages function
    all_packages = package_table.get_all_packages()
    print(f"✓ Get all packages working: Found {len(all_packages)} packages")

    # Test update function
    success = package_table.update_package_status(1, "Delivered")
    if success:
        print("✓ Update status working: Package 1 marked as delivered")

    print("="*50)
    print("Hash table implementation complete and tested!")