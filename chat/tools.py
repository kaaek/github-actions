from .models import Item


def check_stock(name):
    """Look up how many of an item we have."""
    item = Item.objects.filter(name__iexact=name).first()
    if item is None:
        return {"error": f"No item named '{name}' exists in the inventory."}
    return {"name": item.name, "quantity": item.quantity}


def list_items():
    """Return every item in the inventory."""
    items = Item.objects.all()
    return {"items": [{"name": i.name, "quantity": i.quantity} for i in items]}


def add_item(name, quantity):
    """Create a new item, or add to an existing one's stock."""
    item = Item.objects.filter(name__iexact=name).first()
    if item is not None:
        item.quantity += quantity
        item.save()
        return {"name": item.name, "quantity": item.quantity, "created": False}
    item = Item.objects.create(name=name, quantity=quantity)
    return {"name": item.name, "quantity": item.quantity, "created": True}


def remove_stock(name, quantity):
    """Take a quantity out of stock."""
    item = Item.objects.filter(name__iexact=name).first()
    if item is None:
        return {"error": f"No item named '{name}' exists in the inventory."}
    if quantity > item.quantity:
        return {
            "error": f"Cannot remove {quantity}. Only {item.quantity} in stock.",
            "name": item.name,
            "quantity": item.quantity,
        }
    item.quantity -= quantity
    item.save()
    return {"name": item.name, "quantity": item.quantity}


def delete_item(name):
    """Remove an item from the inventory entirely."""
    item = Item.objects.filter(name__iexact=name).first()
    if item is None:
        return {"error": f"No item named '{name}' exists in the inventory."}
    item.delete()
    return {"deleted": name}

def price_items(name, quantity, vat_rate=0):
    """Return the subtotal and total price for an item, optionally including VAT."""
    item = Item.objects.filter(name__iexact=name).first()
    if item is None:
        return {"error": f"No item named '{name}' exists in the inventory."}

    if quantity <= 0:
        return {"error": "Quantity must be positive."}
    if vat_rate < 0:
        return {"error": "VAT rate cannot be negative."}

    subtotal = item.price * quantity
    vat_amount = subtotal * vat_rate / 100
    return {
        "name": item.name,
        "quantity": quantity,
        "unit_price": item.price,
        "subtotal": subtotal,
        "vat_rate": vat_rate,
        "vat_amount": round(vat_amount, 2),
        "total": round(subtotal + vat_amount, 2),
    }

def update_price(name, new_price=None, percent_change=None, amount_change=None):
    """Update an item's unit price, either to an absolute value or by a relative change."""
    item = Item.objects.filter(name__iexact=name).first()
    if item is None:
        return {"error": f"No item named '{name}' exists in the inventory."}

    provided = [v for v in (new_price, percent_change, amount_change) if v is not None]
    if len(provided) != 1:
        return {"error": "Provide exactly one of new_price, percent_change, or amount_change."}

    old_price = item.price
    if new_price is not None:
        updated_price = new_price
    elif percent_change is not None:
        updated_price = old_price * (1 + percent_change / 100)
    else:
        updated_price = old_price + amount_change

    if updated_price < 0:
        return {"error": f"Cannot set price to a negative value ({updated_price})."}

    item.price = round(updated_price)
    item.save()
    return {"name": item.name, "old_price": old_price, "new_price": item.price}


TOOL_DECLARATIONS = [
    {
        "type": "function",
        "name": "check_stock",
        "description": "Look up the current quantity of a single item in the inventory. Use this whenever the user asks whether something is in stock or how many there are.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The name of the item, e.g. 'Hammer'.",
                },
            },
            "required": ["name"],
        },
    },
    {
        "type": "function",
        "name": "list_items",
        "description": "Return every item in the inventory with its quantity. Use this when the user asks what is in stock generally, or asks for a list, rather than about one specific item.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "type": "function",
        "name": "add_item",
        "description": "Add stock to the inventory. If the item does not exist it is created; if it already exists the quantity is added to the existing total. Use this for restocking and for new deliveries.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The name of the item, e.g. 'Hammer'.",
                },
                "quantity": {
                    "type": "integer",
                    "description": "How many units to add. Must be positive.",
                },
            },
            "required": ["name", "quantity"],
        },
    },
    {
        "type": "function",
        "name": "remove_stock",
        "description": "Reduce the quantity of an existing item. Use this when items are sold, shipped or used. This does NOT delete the item; it only lowers the number.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The name of the item, e.g. 'Hammer'.",
                },
                "quantity": {
                    "type": "integer",
                    "description": "How many units to remove. Must be positive.",
                },
            },
            "required": ["name", "quantity"],
        },
    },
    {
        "type": "function",
        "name": "delete_item",
        "description": "Permanently remove an item and its record from the inventory entirely. This is destructive. Only use it when the user clearly wants the item gone, not when they want to reduce its quantity.",
        "parameters": {
            "type": "object",
            "properties": {

                "name": {
                    "type": "string",
                    "description": "The name of the item to delete.",
                },
            },
            "required": ["name"],
        },
    },
    {
        "type": "function",
        "name": "price_items",
        "description": "Calculate the price of a quantity of one inventory item. Include vat_rate when the user gives a VAT or tax percentage; otherwise use 0.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The name of the item, e.g. 'Hammer'.",
                },
                "quantity": {
                    "type": "integer",
                    "description": "How many units requested, must be positive.",
                },
                "vat_rate": {
                    "type": "number",
                    "description": "Optional VAT or sales tax percentage, for example 10 for 10%. Defaults to 0.",
                },
            },
            "required": ["name", "quantity"],
        },
    },
    {
        "type": "function",
        "name": "update_price",
        "description": "Update the unit price of an existing item, either by setting an absolute new price or by applying a relative change. Use percent_change for requests like 'increase the price of X by 20%' (use a negative number to decrease), amount_change for requests like 'raise the price of X by $5' (negative to lower it), or new_price to set the price directly. Provide exactly one of these.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The name of the item, e.g. 'Hammer'.",
                },
                "new_price": {
                    "type": "number",
                    "description": "Set the price to this exact value.",
                },
                "percent_change": {
                    "type": "number",
                    "description": "Percentage to change the price by, e.g. 20 for a 20% increase, -10 for a 10% decrease.",
                },
                "amount_change": {
                    "type": "number",
                    "description": "Flat amount to change the price by, e.g. 5 to increase by 5, -5 to decrease by 5.",
                },
            },
            "required": ["name"],
        },
    },
]

TOOL_FUNCTIONS = {
    "check_stock": check_stock,
    "list_items": list_items,
    "add_item": add_item,
    "remove_stock": remove_stock,
    "delete_item": delete_item,
    "price_items": price_items,
    "update_price": update_price,
}
