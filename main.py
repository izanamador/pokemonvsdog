import streamlit as st
import requests
from PIL import Image, ImageDraw, ImageFont, ImageOps
import io
from st_social_media_links import SocialMediaIcons

# Load the SVG logo from a file
with open("data/logo.svg", "r") as svg_file:
    svg_logo = svg_file.read()

# Embed the SVG logo using HTML
st.markdown(f'<div style="text-align:center">{svg_logo}</div>', unsafe_allow_html=True)
st.subheader("Find out which Pokémon your dog would fight against")

# Function to crop and resize the image
def crop_and_resize(image, size=(255, 255)):
    # Convert the image to RGBA
    image = image.convert("RGBA")
    width, height = image.size

    # Calculate the central crop size
    new_size = min(width, height)
    left = (width - new_size) / 2
    top = (height - new_size) / 2
    right = (width + new_size) / 2
    bottom = (height + new_size) / 2

    # Crop the image to the center
    cropped_image = image.crop((left, top, right, bottom))

    # Resize the cropped image
    resized_image = cropped_image.resize(size, Image.LANCZOS)
    return resized_image

# Upload image
uploaded_image = st.file_uploader("Upload a picture of your dog", type=["jpg", "jpeg", "png"])

# Display the dog's image if uploaded
if uploaded_image is not None:
    st.image(uploaded_image, caption="Your dog's picture")

# Input fields for dog's name and weight
dog_name = st.text_input("Enter your dog's name", "Tobi")
dog_weight = st.number_input("Enter your dog's weight in kg", min_value=1.0, step=0.1)

# Button to find Pokémon opponent (disabled until an image is uploaded)
if st.button("Find Pokémon Opponent", disabled=uploaded_image is None):
    if dog_weight > 0:
        # Convert dog's weight to hectograms
        weight_hectograms = int(dog_weight * 10)

        # Limit search to the first 50 Pokémon to improve speed
        response = requests.get("https://pokeapi.co/api/v2/pokemon?limit=50")
        pokemon_data = response.json()

        # Variable to store the closest matching Pokémon
        closest_pokemon = None
        closest_weight_diff = float('inf')

        # Iterate through each Pokémon to find the closest in weight
        for pokemon in pokemon_data['results']:
            # Get detailed Pokémon information
            pokemon_info = requests.get(pokemon['url']).json()
            pokemon_weight = pokemon_info['weight']

            # Calculate the weight difference
            current_diff = abs(weight_hectograms - pokemon_weight)

            if current_diff < closest_weight_diff:
                closest_weight_diff = current_diff
                closest_pokemon = pokemon_info

        # Display the results
        if closest_pokemon:
            st.write(f"The perfect opponent is **{closest_pokemon['name'].capitalize()}**!")

            # Load the template and fonts
            template = Image.open("data/plantilla.png").convert("RGBA")
            try:
                font_path = "fonts/pokemon_classic.ttf"
                font_name = ImageFont.truetype(font_path, 45)
                font_weight = ImageFont.truetype(font_path, 30)
            except IOError:
                font_name = ImageFont.load_default()
                font_weight = ImageFont.load_default()

            # Create a drawing object for the template
            draw = ImageDraw.Draw(template)

            # Load and process the dog's and Pokémon's images
            dog_image = Image.open(uploaded_image)
            dog_image = crop_and_resize(dog_image)

            pokemon_image_url = closest_pokemon['sprites']['front_default']
            pokemon_image = Image.open(requests.get(pokemon_image_url, stream=True).raw).convert("RGBA").resize((255, 255))

            # Hardcoded positions for the elements
            positions = {
                "dog_name": (300, 490),
                "dog_weight": (230, 565),
                "dog_image": (167, 226),
                "pokemon_name": (990, 490),
                "pokemon_weight": (925, 565),
                "pokemon_image": (855, 232),
            }

            # Calculate text width to center names
            bbox_dog_name = draw.textbbox((0, 0), dog_name, font=font_name)
            bbox_pokemon_name = draw.textbbox((0, 0), closest_pokemon['name'].capitalize(), font=font_name)

            dog_name_width = bbox_dog_name[2] - bbox_dog_name[0]
            pokemon_name_width = bbox_pokemon_name[2] - bbox_pokemon_name[0]

            # Calculate new X positions to center the names
            centered_dog_name = (positions["dog_name"][0] - dog_name_width // 2, positions["dog_name"][1])
            centered_pokemon_name = (positions["pokemon_name"][0] - pokemon_name_width // 2, positions["pokemon_name"][1])

            # Format weights to have one decimal place
            formatted_dog_weight = f"{dog_weight:.1f} kg"
            formatted_pokemon_weight = f"{closest_pokemon['weight'] / 10:.1f} kg"

            # Draw the texts (name and weight) on the template
            draw.text(centered_dog_name, dog_name, font=font_name, fill="white")
            draw.text(positions["dog_weight"], formatted_dog_weight, font=font_weight, fill="white")
            draw.text(centered_pokemon_name, closest_pokemon['name'].capitalize(), font=font_name, fill="white")
            draw.text(positions["pokemon_weight"], formatted_pokemon_weight, font=font_weight, fill="white")

            # Paste images onto the template at specified positions
            template.paste(dog_image, positions["dog_image"], dog_image)
            template.paste(pokemon_image, positions["pokemon_image"], pokemon_image)

            # Convert final image to RGB
            final_template = template.convert("RGB")

            # Display the final result
            st.image(final_template)

            # Create a file for the final image
            buffer = io.BytesIO()
            final_template.save(buffer, format="PNG")
            buffer.seek(0)

            # Button to download the image
            st.download_button(
                label="Download Image",
                data=buffer,
                file_name="pokemon_vs_dog_result.png",
                mime="image/png"
            )

            # Create social media links with st-social-media-links
            social_media_links = [
                "https://x.com/intent/tweet?text=Check%20out%20the%20result%20of%20the%20battle%20between%20my%20dog%20and%20a%20Pokémon!%20%23DogVsPokemon&url=https://pokemonvsperro.streamlit.app",
                "https://www.tiktok.com/@izanhacecosas",
                "https://youtube.com/@quarto.es",
                "https://www.instagram.com/izanhacecosas/"
            ]

            social_media_icons = SocialMediaIcons(social_media_links)
            social_media_icons.render()

    else:
        st.error("Please enter a valid weight.")
