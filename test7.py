import turtle
import colorsys

# Set up the screen
window = turtle.Screen()
window.bgcolor("black")
window.title("Rotating Star Animation")

# Create a turtle
star_turtle = turtle.Turtle()
star_turtle.shape("turtle")
star_turtle.speed(0)  # Fastest speed

# Hide the turtle
star_turtle.hideturtle()

# Define the number of stars and colors
num_stars = 50
hue = 0

# Function to draw a star with dynamic size and color
def draw_star(size, color):
    star_turtle.color(color)
    for _ in range(5):
        star_turtle.forward(size)
        star_turtle.right(144)

# Function to generate stars with different sizes and colors
def draw_rotating_stars():
    global hue
    for i in range(num_stars):
        # Use HSV color system to generate rainbow-like colors
        color = colorsys.hsv_to_rgb(hue, 1, 1)
        hue += 1 / num_stars

        # Convert RGB to Turtle-friendly color format
        color = (color[0], color[1], color[2])
        star_turtle.penup()
        star_turtle.goto(0, 0)  # Move to center
        star_turtle.pendown()

        # Draw star and rotate it
        draw_star(150 + i * 5, color)  # Increment star size more aggressively
        star_turtle.right(360 / num_stars)  # Rotate for each star

# Function to run the animation continuously
def animate():
    try:
        star_turtle.clear()  # Clear the previous stars
        draw_rotating_stars()  # Draw rotating stars
        window.ontimer(animate, 200)  # Slow down animation slightly for better visibility
    except turtle.Terminator:
        pass  # Handle the case when the window is manually closed

# Start the animation
animate()

# Keep the window open until the user closes it
try:
    window.mainloop()  # This will keep the window open

    # Keep the program running even after the mainloop, if needed
    while True:
        pass

except turtle.Terminator:
    print("Turtle window was closed manually.")
