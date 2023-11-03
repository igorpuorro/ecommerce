import calendar
import datetime
import locale
import os
import re
import sys

import pdf2image

from PIL import Image, ImageDraw, ImageFont


def replace_pdf_with_png_extension(file_path):
    if file_path.endswith(".pdf"):
        new_file_path = file_path[:-4] + ".png"

        return new_file_path


def extract_number_from_string(input_string):
    pattern = r'Declaracao_Conteudo-(\d+)\.pdf'

    match = re.search(pattern, input_string)

    if match:
        number = match.group(1)
        return number


def convert_pdf_to_image(pdf_file, output_file, dpi=300):
    pages = pdf2image.convert_from_path(pdf_file, dpi=dpi)

    for page in pages:
        page.save(output_file, 'PNG')


def generate_date_string(location, day, month, year):
    formatted_string = f"{location.ljust(22)}{str(day).rjust(2)}{''.rjust(10)}{str(month).rjust(2)}{''.rjust(12)}{str(year)}"
    return formatted_string


def add_text_to_image(input_image_path, output_image_path, text_to_image_list: list):
    for text_to_image in text_to_image_list:
        try:
            text = text_to_image.get("text")
            coordinates = text_to_image.get("coordinates")
            font_path = text_to_image.get("font_path")
            font_size = text_to_image.get("font_size")
            font_color = text_to_image.get("font_color")

            image = Image.open(input_image_path)
            draw = ImageDraw.Draw(image)

            font = ImageFont.truetype(
                font=font_path, size=font_size, encoding="utf-8"
            )

            x, y = coordinates
            fill = font_color
            draw.text((x, y), text, fill=fill, font=font)
            # draw.text((x, y + 1634), text, fill=fill, font=font)

            image.save(output_image_path)

        except Exception as e:
            print(f"An error occurred: {e}")

    print(f"Text added to {output_image_path}")


def merge_horizontal_halves(file1_name, file2_name, output_file_name):
    try:
        img1 = Image.open(file1_name)
        img2 = Image.open(file2_name)

        # Get the dimensions of the first image
        width, height = img1.size

        # Crop the top half of the first image
        top_half = img1.crop((0, 0, width, height // 2))

        # Crop the bottom half of the second image
        bottom_half = img2.crop((0, height // 2, width, height))

        # Create a new image with the same dimensions as the original images
        merged_image = Image.new('RGB', (width, height))

        # Paste the top and bottom halves onto the new image
        merged_image.paste(top_half, (0, 0))
        merged_image.paste(bottom_half, (0, height // 2))

        # Save the merged image to the output file
        merged_image.save(output_file_name, "PNG")

        print(f"Merged image saved as {output_file_name}")
    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == '__main__':
    locale.setlocale(locale.LC_ALL, "pt_BR")

    if len(sys.argv) < 3:
        print(
            f"Usage: python3 {sys.argv[0]} <pdf_file_1_path> <pdf_file_2_path>"
        )

        sys.exit(1)

    image_dictory = os.path.join("..", "images")

    if not os.path.exists(image_dictory):
        os.makedirs(image_dictory)

    pdf_file_1_path = sys.argv[1]
    pdf_file_2_path = sys.argv[2]

    pdf_file_1 = os.path.basename(pdf_file_1_path)
    pdf_file_2 = os.path.basename(pdf_file_2_path)

    png_file_1_path = os.path.join(
        image_dictory,
        replace_pdf_with_png_extension(os.path.basename(pdf_file_1_path))
    )
    png_file_2_path = os.path.join(
        image_dictory,
        replace_pdf_with_png_extension(os.path.basename(pdf_file_2_path))
    )

    merged_png_path = os.path.join(
        image_dictory,
        f"merged-{extract_number_from_string(pdf_file_1)}_{extract_number_from_string(pdf_file_2)}.png"
    )

    convert_pdf_to_image(pdf_file_1_path, png_file_1_path)
    convert_pdf_to_image(pdf_file_2_path, png_file_2_path)

    month_name = calendar.month_name[10].lower()
    localized_month_name = month_name.translate("pt_BR")

    current_date = datetime.date.today()

    date_string = generate_date_string(
        "São Paulo",
        current_date.day,
        localized_month_name,
        current_date.year
    )

    font_path = "arial-unicode-ms.ttf"
    font_color = (0, 0, 0)

    add_text_to_image(
        png_file_1_path,
        png_file_1_path,
        text_to_image_list=[
            {
                "text": extract_number_from_string(pdf_file_1),
                "coordinates": (130, 190),
                "font_path": font_path,
                "font_size": 28,
                "font_color": font_color
            },
            {
                "text": date_string,
                "coordinates": (130, 1373),
                "font_path": font_path,
                "font_size": 34,
                "font_color": font_color
            },
            {
                "text": date_string,
                "coordinates": (130, 3007),
                "font_path": font_path,
                "font_size": 34,
                "font_color": font_color
            }
        ]
    )

    add_text_to_image(
        png_file_2_path,
        png_file_2_path,
        text_to_image_list=[
            {
                "text": extract_number_from_string(pdf_file_2),
                "coordinates": (130, 1825),
                "font_path": font_path,
                "font_size": 28,
                "font_color": font_color
            },
            {
                "text": date_string,
                "coordinates": (130, 1373),
                "font_path": font_path,
                "font_size": 34,
                "font_color": font_color
            },
            {
                "text": date_string,
                "coordinates": (130, 3007),
                "font_path": font_path,
                "font_size": 34,
                "font_color": font_color
            }
        ]
    )

    merge_horizontal_halves(png_file_1_path, png_file_2_path, merged_png_path)

    os.remove(png_file_1_path)
    os.remove(png_file_2_path)
