import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'swarmgrid'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
        (os.path.join('share', package_name, 'worlds'), glob('worlds/*.world')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Srirag',
    maintainer_email='you@example.com',
    description='Decentralized 5-robot AMR warehouse fleet-coordination system (SwarmGrid).',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            # Box 1-2: init + task generation
            'task_manager = swarmgrid.auction.task_manager:main',
            # Box 3: decentralized auction
            'robot_agent = swarmgrid.auction.robot_agent:main',
            # Box 4: path planning (A* / Cooperative A*)
            'path_planner = swarmgrid.planning.path_planner:main',
            # Box 5: PIBT + space-time reservations
            'pibt_coordinator = swarmgrid.coordination.pibt_coordinator:main',
            'reservation_table = swarmgrid.coordination.reservation_table:main',
            # Box 6: safety firewall (final authority)
            'action_firewall = swarmgrid.safety.action_firewall:main',
            # Box 7-8: execution + monitoring
            'task_executor = swarmgrid.monitoring.task_executor:main',
            'fleet_monitor = swarmgrid.monitoring.fleet_monitor:main',
            # Box 8-9: failure detection + reallocation
            'failure_detector = swarmgrid.failure.failure_detector:main',
            # Box 10: rescue + towing
            'rescue_controller = swarmgrid.rescue.rescue_controller:main',
        ],
    },
)
