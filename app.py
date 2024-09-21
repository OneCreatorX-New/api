from flask import Flask, request, jsonify
import asyncio
from pyppeteer import launch
import re

app = Flask(__name__)

URL_PATTERNS = [
    r'1a-1791\.com/video/.*\.mp4',
    r'dailymotion\.com/embed/video/',
    r'ok\.ru/videoembed/',
    r'geo\.dailymotion\.com/player\.html'
]

async def capture_url(url):
    browser = await launch(args=['--no-sandbox'])
    page = await browser.newPage()
    captured_urls = set()

    async def intercept_request(request):
        if any(re.search(pattern, request.url) for pattern in URL_PATTERNS):
            captured_urls.add(request.url)
        await request.continue_()

    await page.setRequestInterception(True)
    page.on('request', lambda req: asyncio.ensure_future(intercept_request(req)))

    try:
        await asyncio.wait_for(page.goto(url), timeout=5.0)
    except asyncio.TimeoutError:
        pass

    await browser.close()
    return list(captured_urls)

@app.route('/capture', methods=['POST'])
def capture():
    url = request.json.get('url')
    if not url:
        return jsonify({'error': 'URL is required'}), 400

    captured_urls = asyncio.get_event_loop().run_until_complete(capture_url(url))

    if captured_urls:
        return jsonify({'captured_url': captured_urls[0]})
    else:
        return jsonify({'message': 'No matching URLs found'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
