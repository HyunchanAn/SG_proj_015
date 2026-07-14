import numpy as np

def compute(w_angle, g_angle):
    w_props = {"g": 72.8, "d": 21.8, "p": 51.0}
    g_props = {"g": 64.0, "d": 34.0, "p": 30.0}
    
    def get_xy(props, angle):
        rad = np.radians(angle)
        y = (props["g"] * (1 + np.cos(rad))) / (2 * np.sqrt(props["d"]))
        x = np.sqrt(props["p"] / props["d"])
        return x, y
        
    x_w, y_w = get_xy(w_props, w_angle)
    x_g, y_g = get_xy(g_props, g_angle)
    
    slope = (y_w - y_g) / (x_w - x_g)
    intercept = y_w - slope * x_w
    
    slope = max(0.0, float(slope))
    intercept = max(0.0, float(intercept))
    
    return intercept**2 + slope**2

print(f"Original: {compute(68.75, 88.83):.2f}")
print(f"Swapped: {compute(88.83, 68.75):.2f}")
print(f"Both 70: {compute(70, 70):.2f}")
