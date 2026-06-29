import math

def calculate_distance(point1, point2):
     # Calculate the Euclidean distance between two points in 2D space.
    return math.hypot(point1.x - point2.x , point1.y - point2.y)

