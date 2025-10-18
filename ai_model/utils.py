def calculate_percentage(total_quantity, part_quantity):
    if total_quantity == 0:
        return 0 
    percentage = (part_quantity/total_quantity) * 100
    return round(percentage, 2)