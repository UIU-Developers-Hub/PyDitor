import heapq

class Node:
    def __init__(self, position, parent=None, g=0, h=0, f=0):
        self.position = position  # Position in the grid (x, y)
        self.parent = parent  # Parent node for path reconstruction
        self.g = g  # Cost from start to current node
        self.h = h  # Heuristic cost from current node to goal
        self.f = f  # Total cost (g + h)

    def __lt__(self, other):
        return self.f < other.f

def a_star_search(grid, start, goal):
    def heuristic(a, b):
        # Manhattan distance heuristic for grid-based pathfinding
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    # Create the start and goal node
    start_node = Node(start, None, 0, 0, 0)
    goal_node = Node(goal, None, 0, 0, 0)

    # Initialize both open and closed lists
    open_list = []
    closed_list = set()

    # Add the start node
    heapq.heappush(open_list, start_node)

    # Directions for moving in the grid (up, down, left, right)
    directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]

    # Loop until you find the goal
    while open_list:
        # Get the current node with the lowest f score
        current_node = heapq.heappop(open_list)

        # If goal is reached, reconstruct the path
        if current_node.position == goal_node.position:
            path = []
            while current_node is not None:
                path.append(current_node.position)
                current_node = current_node.parent
            return path[::-1]  # Return the reversed path

        # Add the current node to the closed list
        closed_list.add(current_node.position)

        # Explore neighbors
        for direction in directions:
            neighbor_position = (current_node.position[0] + direction[0],
                                 current_node.position[1] + direction[1])

            # Check if neighbor is within grid bounds
            if (neighbor_position[0] < 0 or neighbor_position[0] >= len(grid) or
                neighbor_position[1] < 0 or neighbor_position[1] >= len(grid[0])):
                continue  # Out of bounds

            # Check if the neighbor is walkable
            if grid[neighbor_position[0]][neighbor_position[1]] != 0:
                continue  # Blocked cell

            # Check if neighbor is in the closed list
            if neighbor_position in closed_list:
                continue

            # Calculate costs
            g = current_node.g + 1  # Move cost
            h = heuristic(neighbor_position, goal_node.position)
            f = g + h

            # Check if the neighbor is already in the open list with a lower cost
            neighbor_node = Node(neighbor_position, current_node, g, h, f)
            if any(open_node.position == neighbor_node.position and open_node.g <= neighbor_node.g for open_node in open_list):
                continue

            # Add the neighbor to the open list
            heapq.heappush(open_list, neighbor_node)

    return None  # No path found

# Example usage
if __name__ == "__main__":
    # 0 = walkable, 1 = blocked
    grid = [
        [0, 0, 0, 1, 0, 0, 0],
        [0, 1, 0, 1, 0, 1, 0],
        [0, 1, 0, 1, 0, 1, 0],
        [0, 0, 0, 0, 0, 1, 0],
        [0, 1, 1, 1, 0, 0, 0],
        [0, 0, 0, 1, 1, 1, 1],
        [0, 0, 0, 0, 0, 0, 0]
    ]

    start = (0, 0)
    goal = (6, 6)
    
    path = a_star_search(grid, start, goal)
    if path:
        print("Path found:", path)
    else:
        print("No path found.")
