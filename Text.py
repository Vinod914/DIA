import requests
from bs4 import BeautifulSoup
from io import BytesIO
from PIL import Image
import pytesseract
import pandas as pd
import re


def extract_image_links(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    img_tags = soup.find_all("img")
    img_links = []
    for img in img_tags:
        img_link = img.get("src")
        if img_link.endswith(".jpg") or img_link.endswith(".jpeg") or img_link.endswith(".png"):
            img_links.append(img_link)
    return img_links, soup


def extract_text_from_image(image):
    try:
        image = Image.open(BytesIO(image))
        text = pytesseract.image_to_string(image)
        return text.strip()  # Remove leading/trailing white spaces from the extracted text
    except pytesseract.TesseractNotFoundError:
        print("Tesseract is not installed or not found in the system's PATH.")
        return None
    except Exception as e:
        print(f"Error in image processing: {e}")
        return None


def fetch_text_from_url(url):
    img_links, soup = extract_image_links(url)
    text_content = soup.get_text()
    image_alt_text = []
    for img in soup.find_all('img'):
        if 'alt' in img.attrs:
            image_alt_text.append(img.attrs['alt'])
    text_content += ' '.join(image_alt_text)
    return text_content


def remove_non_alpha(text):
    return re.sub(r'[^a-zA-Z\s]', '', text)


def is_word_present(sentence, word):
    # Split the sentence into individual words
    words = sentence.split()

    # Iterate over the words and check for a match
    for w in words:
        # Remove any punctuation marks from the word
        clean_word = ''.join(c for c in w if c.isalnum())

        # Compare the clean word with the target word
        if clean_word.lower() == word.lower():
            return True

    # No match found
    return False


def find_biased_sentences(text, biased_words):
    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', text)
    biased_sentences = []
    for sentence in sentences:
        for word in biased_words:
            if is_word_present(sentence, word):
                biased_sentences.append((word, sentence))
                break
    return biased_sentences


def print_biased_sentences(biased_sentences):
    if biased_sentences:
        print("Biased sentences:")
        for word, sentence in biased_sentences:
            highlighted_sentence = highlight_word_in_sentence(word, sentence)
            print(f"\033[91mBiased word: {word}\033[0m")
            print(highlighted_sentence)
            print()
    else:
        print("No biased sentences found.")


def highlight_word_in_sentence(word, sentence):
    highlighted_sentence = sentence.lower().replace(word.lower(), f"\033[91m{word.upper()}\033[0m")
    return highlighted_sentence


url = 'https://avinuty.ac.in'
text_content = fetch_text_from_url(url)
text_content = remove_non_alpha(text_content)

df = pd.read_excel('gender_biased_words.xlsx', sheet_name='word')
biased_words = df['word'].tolist()

biased_sentences = find_biased_sentences(text_content, biased_words)
print_biased_sentences(biased_sentences)
