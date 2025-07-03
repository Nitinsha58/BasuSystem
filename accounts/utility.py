import urllib.parse

def generate_whatsapp_link(message, phone):
    base_url = f"https://wa.me/{phone}?text="
    encoded_message = urllib.parse.quote(message)
    return base_url + encoded_message