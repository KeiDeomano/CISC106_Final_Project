from bakery import assert_equal
from dataclasses import dataclass
from drafter import *

set_website_style("terminal")
set_website_title("Image Steganography")
set_site_information(
    author="Kei Deomano",
    description="Image Steganography Encryption and Decryption.",
    sources="",
    planning=[],
    links=[]
)
hide_debug_information()
set_website_framed(False)


@dataclass
class Encoded:
    message: str
    encrypted: list[str]
    image: Picture

@dataclass
class State:
    message: str
    encrypted: list[str]
    image: Picture
    history: list[Encoded]
    
    
def toAscii(message: str) -> list[str]:
    """
    Converts a string into 8-bit binary ASCII values.
    
    Arguments:
        message (str): The string to be converted.

    Returns:
        list[str]: A list of strings representing the message as 8-bit ASCII values.
    """
    values = []
    for character in message:
        values.append(f"{ord(character):08b}")
    return values

assert_equal(toAscii("H"), ["01001000"])
assert_equal(toAscii("Hii"), ["01001000", "01101001", "01101001"])


def fromAscii(binaries: list[str]) -> str:
    """
    Converts a list of 8-bit binary values into a string.
    
    Arguments:
        binaries (list[str]): The list of 8-bit binary values, each representing an ASCII value.
        
    Returns:
        str: A message representing the given list of 8-bit binary ASCII values as characters.
    """
    asciis = []
    for binary in binaries:
        asciis.append(int(binary, 2))
    message = ""
    for value in asciis:
        message += chr(value)
    return message

assert_equal(fromAscii(["01001000"]), "H")
assert_equal(fromAscii(["01001000", "01101001", "01101001"]), "Hii")


def codeColorValue(color_val: int) -> int:
    """
    Shifts an RGB value by one.
    
    Arguments:
        rgb (int): An R, G, or B value of a pixel between 0 - 255.
        
    Returns:
        int: The color value shifted by one.
    """
    if not color_val:
        return 1
    return color_val - 1

assert_equal(codeColorValue(0), 1)
assert_equal(codeColorValue(1), 0)
assert_equal(codeColorValue(250), 249)
assert_equal(codeColorValue(255), 254)


def nextPixel(state: State, text_index: int, pixel: int) -> list[int]:
    """
    Returns the coordinates of the next pixel. Moves left to right, top to bottom.
    
    Arguments:
        state (State):
        text_index (int):
        pixel(int):
        
    Returns:
        list[int]: The x, y coordinates of the next pixel.
    """
    width = state.image.width

    x = (text_index * 3 + pixel) % width
    y = (text_index * 3 + pixel) // width
    
    if x + 1 < width: # move right
        return [x + 1, y]
    return [0, y + 1] # move down

assert_equal(nextPixel(State("",[],Picture.new(80,20,"salmon"),[]),0,0), [1,0])


def encodeCharacter(state: State, character: str, text_index: int, last: bool):
    """
    Encodes a single 8-bit ASCII value into three pixels using image steganography.
    
    Arguments:
        state (State): The state containing the image to encode.
        character (str): The character to encode into into the image.
        text_index (int): The character index of the overall message to hide in the image.
        last (bool): If the character is the last in the message.
    """    
    bit = 0
    for pixel in range(3):
        x, y = nextPixel(state, text_index, pixel)
        current_pixel = state.image.get_pixel(x, y)
        new_pixel = list(current_pixel)
        for rgb in range(3):
            if bit < 8:
                if int(character[bit]): # binary bit = 1, make odd
                    if not current_pixel[rgb] % 2: # color value is even
                        new_pixel[rgb] = codeColorValue(new_pixel[rgb])
                else: # binary bit = 0, keep even
                    if current_pixel[rgb] % 2: # color value is odd
                        new_pixel[rgb] = codeColorValue(new_pixel[rgb])
            bit += 1
        state.image.set_pixel(x, y, new_pixel)
        
    x, y = nextPixel(state, text_index, 2)
    if last: # last rgb value ODD
        if not state.image.get_pixel(x, y)[2] % 2: # color value is even
            last_pixel = list(state.image.get_pixel(x, y))
            last_pixel[2] = codeColorValue(last_pixel[2])
            state.image.set_pixel(x, y, last_pixel)
    else: # last rgb value EVEN
        if state.image.get_pixel(x, y)[2] % 2: # color value is odd
            last_pixel = list(state.image.get_pixel(x, y))
            last_pixel[2] = codeColorValue(last_pixel[2])
            state.image.set_pixel(x, y, last_pixel)
            
#encodeCharacter() can't be unit tested because it returns nothing


def decodeCharacter(state: State, text_index: int) -> bool:
    """
    Decodes a single character from three pixels using steganography.
    
    Arguments:
        state (State): The website state containing the image to decode.
        text_index (int): The character index of the overall hidden message in the image.
        
    Returns:
        bool: If the character is the last encoded within the state's image.
    """
    binary = ""
    for pixel in range(3):
        x, y = nextPixel(state, text_index, pixel)
        current_pixel = state.image.get_pixel(x, y)    
        for rgb in range(3):
            if len(binary) < 8:
                if current_pixel[rgb] % 2: # color value is odd, binary bit = 1
                    binary += "1"
                else: # color value is even, binary bit = 0
                    binary += "0"
    state.encrypted.append(binary)
    
    x, y = nextPixel(state, text_index, 2)
    if not state.image.get_pixel(x, y)[2] % 2: # color value is even
        return True # continue decoding
    return False # message is finished

assert_equal(decodeCharacter(State("", [], Picture.new(80,20,"aqua"), []), 0), False)
assert_equal(decodeCharacter(State("", [], Picture.new(80,20,"salmon"), []), 0), True)
    
    
@route
def index(state: State, error="") -> Page:
    """
    The website's central navigation and image steganography input page.
    
    Arguments:
        state (State): The website state.
        error (str): An error message to display.
    Returns:
        Page: Navigation to encrypt, decrypt, see history, and read about image steganography.
            Also has input for a message to encrypt and a file upload to encrypt/decrypt.
    """
    return Page(state, [
        Header("Image Steganography"),
        Header(error, style_color="crimson"),
        Header("Encryption Message:", 3),
        TextArea("message", state.message),
        "\n",
        Header("Image:", 3),
        FileUpload("image", accept=[".png",".jpg",".jpeg"]),
        "\n\n",
        Button("Encrypt", "encrypt_result"),
        Button("Decrypt", "decrypt_result"),
        "\n\n",
        Button("History", "history"),
        "\n\n",
        Link("How does this work?", "info")
        ])

assert_equal(index(State("", [], None, [])),
            Page(State("", [], None, []), [
            Header("Image Steganography"),
            Header("", style_color="crimson"),
            Header("Encryption Message:", 3),
            TextArea("message", ""),
            "\n",
            Header("Image:", 3),
            FileUpload("image", accept=[".png",".jpg",".jpeg"]),
            "\n\n",
            Button("Encrypt", "encrypt_result"),
            Button("Decrypt", "decrypt_result"),
            "\n\n",
            Button("History", "history"),
            "\n\n",
            Link("How does this work?", "info")
            ]))
assert_equal(index(State("", [], None, []), "Error!"),
            Page(State("", [], None, []), [
            Header("Image Steganography"),
            Header("Error!", style_color="crimson"),
            Header("Encryption Message:", 3),
            TextArea("message", ""),
            "\n",
            Header("Image:", 3),
            FileUpload("image", accept=[".png",".jpg",".jpeg"]),
            "\n\n",
            Button("Encrypt", "encrypt_result"),
            Button("Decrypt", "decrypt_result"),
            "\n\n",
            Button("History", "history"),
            "\n\n",
            Link("How does this work?", "info")
            ]))


@route
def encrypt_result(state: State, message="", image=None) -> Page:
    """
    Displays an encrypted image using steganography for the user to download. Returns
        to the main page if no image is given or if the message is too long.
    
    Arguments:
        state (State): The website's state.
        message (str): The message to encrypt.
        image (Picture): The image to encrypt the message in.
    Returns:
        Page: Displays the encrypted image and a download link. 
    """
    state.message = message
    if not image:
        return index(state, "Please provide an image file.")
    state.image = image 
    if len(message) > (state.image.height * state.image.width):
        return index(state, "Message too long!\nMaximum character length for given image is " +
                     str(state.image.height*state.image.width // 3))
    state.encrypted = toAscii(message)
    for text_index, character in enumerate(state.encrypted):
        encodeCharacter(state, character, text_index, text_index == len(state.encrypted) - 1)
    state.history.append(Encoded(state.message, state.encrypted, state.image))
    
    return Page(state, [
        Picture(state.image),
        Download("Download Encrypted Image", "encrypted_image.png", state.image),
        "\n\n",
        Button("Back", "index")
        ])

assert_equal(encrypt_result(State("", [], None, []), "", None),
            Page(State("", [], None, []), [
            Header("Image Steganography"),
            Header("Please provide an image file.", style_color="crimson"),
            Header("Encryption Message:", 3),
            TextArea("message", ""),
            "\n",
            Header("Image:", 3),
            FileUpload("image", accept=[".png",".jpg",".jpeg"]),
            "\n\n",
            Button("Encrypt", "encrypt_result"),
            Button("Decrypt", "decrypt_result"),
            "\n\n",
            Button("History", "history"),
            "\n\n",
            Link("How does this work?", "info")
            ]))
assert_equal(encrypt_result(State("", [], None, []), "AAAA", Picture.new(3,1,"aqua")),
            Page(State("AAAA", [], Picture.new(3,1,"aqua"), []), [
            Header("Image Steganography"),
            Header("Message too long!\nMaximum character length for given image is 1", style_color="crimson"),
            Header("Encryption Message:", 3),
            TextArea("message", "AAAA"),
            "\n",
            Header("Image:", 3),
            FileUpload("image", accept=[".png",".jpg",".jpeg"]),
            "\n\n",
            Button("Encrypt", "encrypt_result"),
            Button("Decrypt", "decrypt_result"),
            "\n\n",
            Button("History", "history"),
            "\n\n",
            Link("How does this work?", "info")
            ]))


@route
def decrypt_result(state: State, message="", image=None) -> Page:
    """
    Displays an decrypted message from image steganography for the user to download. Returns
        to the main page if no image is given.
    
    Arguments:
        state (State): The website's state.
        message (str): The message to encrypt for returning to the main page.
        image (Picture): The image to decrypt the message from.
    Returns:
        Page: Displays the decrypted message and a .txt download link. 
    """
    state.message = message
    if not image:
        return index(state, "Please provide an image file.")
    state.image = image 
    state.encrypted = []
    proceed = True
    while proceed:
        proceed = decodeCharacter(state, len(state.encrypted))
    state.message = fromAscii(state.encrypted)
    state.history.append(Encoded(state.message, state.encrypted, state.image))
    
    return Page(state, [
        "Your image's hidden message*:",
        Paragraph(state.message),
        "\n",
        Download("Download the message", "message.txt", state.message),
        "\n\n",
        Button("Back", "index"),
        "\n\n*Your image may not have a hidden message!"
        ])

assert_equal(decrypt_result(State("", [], None, []), "", None),
            Page(State("", [], None, []), [
            Header("Image Steganography"),
            Header("Please provide an image file.", style_color="crimson"),
            Header("Encryption Message:", 3),
            TextArea("message", ""),
            "\n",
            Header("Image:", 3),
            FileUpload("image", accept=[".png",".jpg",".jpeg"]),
            "\n\n",
            Button("Encrypt", "encrypt_result"),
            Button("Decrypt", "decrypt_result"),
            "\n\n",
            Button("History", "history"),
            "\n\n",
            Link("How does this work?", "info")
            ]))
assert_equal(decrypt_result(State("", [], None, []), "", Picture.new(3,2,"aqua")),
            Page(State("m", ["01101101"], Picture.new(3,2,"aqua"), [Encoded("m", ["01101101"], Picture.new(3,2,"aqua"))]), [
            "Your image's hidden message*:",
            Paragraph("m"),
            "\n",
            Download("Download the message", "message.txt", "m"),
            "\n\n",
            Button("Back", "index"),
            "\n\n*Your image may not have a hidden message!"
            ]))


@route
def history(state: State) -> Page:
    """
    Displays the use history of encrypted/decrypted images and their respective messages in a table.
    
    Arguments:
        state (State): The website's state holding the history in a list attribute.
    Returns:
        Page: Shows the use history in a table with encrypted/decrypted messages and their respective images. 
    """
    if not state.history:
        return Page(state, [
            Header("History"),
            Header("No history to display.", 3),
            Button("Clear", "clear_history"),
            "\n\n",
            Button("Back", "index")
        ])
    
    rows = []
    for record in state.history:
        rows.append([record.message, record.image])  
    return Page(state, [
        Header("History"),
        Table(rows, ["Message", "Encrypted Image"]),
        Button("Clear", "clear_history"),
        "\n\n",
        Button("Back", "index")
        ])

assert_equal(history(State("", [], None, [])),
            Page(State("", [], None, []), [
            Header("History"),
            Header("No history to display.", 3),
            Button("Clear", "clear_history"),
            "\n\n",
            Button("Back", "index")
        ]))

@route
def clear_history(state: State) -> Page:
    """
    Clears the use history of encrypted/decrypted images and their respective messages.
    
    Arguments:
        state (State): The website's state holding the history in a list attribute.
    Returns:
        Page: Shows a message reporting no history to display. 
    """
    state.history = []
    return history(state)

assert_equal(clear_history(State("", [], None, [Encoded("", [], None)])),
            Page(State("", [], None, []), [
            Header("History"),
            Header("No history to display.", 3),
            Button("Clear", "clear_history"),
            "\n\n",
            Button("Back", "index")
        ]))
assert_equal(clear_history(State("", [], None, [])),
             Page(State("", [], None, []), [
            Header("History"),
            Header("No history to display.", 3),
            Button("Clear", "clear_history"),
            "\n\n",
            Button("Back", "index")
        ]))


@route
def info(state: State) -> Page:
    """
    Text explanation of the website's image steganography algorithm.
    
    Arguments:
        state (State): The website's state.
        
    Returns:
        Page: Displays text explaining the website's image steganography algorithm.
    """
    return Page(state, [
        Header("Image Steganography How-To"),
        Text("Following"),
        Link("this.", "https://www.geeksforgeeks.org/python/image-based-steganography-using-python/"),
        Paragraph("Image steganography hides messages in images by very slightly changing pixel RGB values."),
        Header("Encryption", 3),
        Paragraph("Each character is first converted to ASCII value, then 8-bit binary representation."),
        Paragraph("Then, starting from the top left-most pixel, each character is encoded into 3 pixels."),
        Paragraph("A 0 corresponds to an even RGB value; 1 is odd."),
        Paragraph("If necessary, each RGB value is adjusted by 1 to match."),
        Paragraph("The 3rd pixel's B value is odd to signal the message's end, even to continue."),
        Header("Decryption", 3),
        Paragraph("Each image is read from the top left-most pixel, 3 pixels at a time."),
        Paragraph("Even RGB values are 0s, odds are 1s. If the 3rd pixel's B value is odd, the message is done."),
        Paragraph("From 8-bit binary to ASCII value to character, they're combined into the whole hidden message."),
        Button("Back", "index")
        ])

assert_equal(info(State("",[],Picture.new(80,20,"salmon"),[])),
        Page(State("",[],Picture.new(80,20,"salmon"),[]), [
        Header("Image Steganography How-To"),
        Text("Following"),
        Link("this.", "https://www.geeksforgeeks.org/python/image-based-steganography-using-python/"),
        Paragraph("Image steganography hides messages in images by very slightly changing pixel RGB values."),
        Header("Encryption", 3),
        Paragraph("Each character is first converted to ASCII value, then 8-bit binary representation."),
        Paragraph("Then, starting from the top left-most pixel, each character is encoded into 3 pixels."),
        Paragraph("A 0 corresponds to an even RGB value; 1 is odd."),
        Paragraph("If necessary, each RGB value is adjusted by 1 to match."),
        Paragraph("The 3rd pixel's B value is odd to signal the message's end, even to continue."),
        Header("Decryption", 3),
        Paragraph("Each image is read from the top left-most pixel, 3 pixels at a time."),
        Paragraph("Even RGB values are 0s, odds are 1s. If the 3rd pixel's B value is odd, the message is done."),
        Paragraph("From 8-bit binary to ASCII value to character, they're combined into the whole hidden message."),
        Button("Back", "index")
        ]))


start_server(State("Enter message to encrypt here!", [], None, []))

