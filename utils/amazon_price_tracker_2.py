import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time

# ===== CONFIG =====
URL = "https://www.amazon.in/Crucial-BX500-NAND-2-5-Inch-Internal/dp/B07YD579WM/ref=sr_1_2?crid=36RRRQVQ5MWEK&dib=eyJ2IjoiMSJ9.W25BKw_oWMGeCGKz3mxcSQVwVZJAGmRQUtDTdRyyzi-MKj3oLDT6TOvgqvaJF2Npd38XhNn63zUTazdFXlys1nB20Gr30AmjZsmTb2Kdu-R3SS0tN7ZAYPsOCCBy0gr8xtb07ogTWBXH-furqbPGP_9Q-ixdTaRq-QcFD5KC09pSP-KFcAd9trnbX8JN7oPaVfWa2mOwimLAdkHjfNoSXT4mnYAcwb12culiTj2YLHY.naEb4cdEBQMWdaH4ASxSciiBzDRcPC9Np0j2EO-ATj4&dib_tag=se&keywords=2.5%2Binch%2Bsata%2Bhdd&qid=1757223745&refinements=p_n_g-1004209391091%3A1464350031&rnid=1464345031&sprefix=2.5%2Bin%2Caps%2C251&sr=8-2&th=1"  # replace with your product URL
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9"
}
THRESHOLD_PRICE = 20000.0  # your target price
CHECK_INTERVAL = 60 * 60  # check every 1 hour

# ===== EMAIL CONFIG =====
SENDER_EMAIL = "youremail@gmail.com"
SENDER_PASSWORD = "your-app-password"   # use App Password for Gmail
RECEIVER_EMAIL = "targetemail@gmail.com"


def get_price():
    """Scrape Amazon product page and return price as float."""
    response = requests.get(URL, headers=HEADERS)
    soup = BeautifulSoup(response.text, "html.parser")

    # Amazon often uses this id for price
    price_tag = soup.find("span", {"class": "a-price-whole"})
    if not price_tag:
        raise ValueError("Could not find price on the page.")

    price_text = price_tag.get_text().replace(",", "").strip()
    return float(price_text)


def send_notification(price):
    """Send email when price drops below threshold."""
    subject = "Amazon Price Drop Alert!"
    body = f"The price dropped to ₹{price}\nCheck here: {URL}"

    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        server.quit()
        print("Notification sent!")
    except Exception as e:
        print("Failed to send email:", e)


def track_price():
    """Main loop for tracking."""
    while True:
        try:
            price = get_price()
            print(f"Current Price: ₹{price}")
            if price < THRESHOLD_PRICE:
                send_notification(price)
                break  # stop after alert, or remove this if you want continuous monitoring
        except Exception as e:
            print("Error:", e)

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    track_price()
