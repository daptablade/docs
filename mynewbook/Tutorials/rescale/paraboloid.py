from datetime import datetime

def f_xy(x, y):
    
    out = {}
    out["f_xy"] = (x - 3.0) ** 2 + x * y + (y + 4.0) ** 2 - 3.0

    message = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}: Compute paraboloid f(x:{str(x)},y:{str(y)}) = {str(out['f_xy'])}."
    out["message"] = message
    
    return out
    
if __name__ == "__main__":
    out = f_xy(5.0,5.0)
    print(out["message"])