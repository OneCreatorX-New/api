from flask import Flask, request, jsonify
from flask_cors import CORS
import asyncio
from pyppeteer import launch
import re
import logging
from logging.handlers import RotatingFileHandler
import time

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.DEBUG)
handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=3)
handler.setLevel(logging.DEBUG)
app.logger.addHandler(handler)

URL_PATTERNS = [
    r'1a-1791\.com/video/.*\.mp4',
    r'dailymotion\.com/embed/video/',
    r'ok\.ru/videoembed/',
    r'geo\.dailymotion\.com/player\.html'
]

async def capture_url(url):
    app.logger.info(f"Starting capture for URL: {url}")
    try:
        browser = await launch(args=['--no-sandbox', '--disable-setuid-sandbox'])
        page = await browser.newPage()
        captured_urls = set()

        async def intercept_request(request):
            if any(re.search(pattern, request.url) for pattern in URL_PATTERNS):
                captured_urls.add(request.url)
                app.logger.debug(f"Captured URL: {request.url}")
            await request.continue_()

        await page.setRequestInterception(True)
        page.on('request', lambda req: asyncio.ensure_future(intercept_request(req)))

        try:
            await asyncio.wait_for(page.goto(url), timeout=10.0)
        except asyncio.TimeoutError:
            app.logger.warning(f"Timeout occurred while loading {url}")

        await browser.close()
        app.logger.info(f"Capture completed for URL: {url}")
        return list(captured_urls)
    except Exception as e:
        app.logger.error(f"Error during capture: {str(e)}")
        return []

@app.route('/capture', methods=['POST'])
def capture():
    start_time = time.time()
    app.logger.info("Received capture request")
    
    url = request.json.get('url')
    if not url:
        app.logger.warning("Request received without URL")
        return jsonify({'error': 'URL is required'}), 400

    try:
        captured_urls = asyncio.get_event_loop().run_until_complete(capture_url(url))

        if captured_urls:
            app.logger.info(f"Captured URL: {captured_urls[0]}")
            response = {'captured_url': captured_urls[0]}
        else:
            app.logger.info("No matching URLs found")
            response = {'message': 'No matching URLs found'}

        elapsed_time = time.time() - start_time
        app.logger.info(f"Request processed in {elapsed_time:.2f} seconds")
        return jsonify(response)
    except Exception as e:
        app.logger.error(f"Error processing request: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)
