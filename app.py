addEventListener('fetch', e => e.respondWith(handleRequest(e.request)))

async function handleRequest(request) {
  try {
    const ua = request.headers.get('User-Agent');
    if (!ua || !ua.includes('Roblox')) throw new Error('Invalid User-Agent');

    const url = new URL(request.url);
    const t = parseInt(url.searchParams.get('t'), 10);
    const ct = Math.floor(Date.now() / 1000);
    
    if (isNaN(t) || ct - t > 3) throw new Error('Invalid timestamp');

    const sl = url.searchParams.get('sl');
    if (!sl || !sl.match(/^[a-zA-Z0-9-_,]+$/)) throw new Error('Invalid slug');

    const slugs = sl.split('-');
    let fullContent = '';

    for (const slug of slugs) {
      const content = await fetchPasteContent(slug);
      fullContent += content.trim() + '\n'; // Add newline between contents
    }

    fullContent = fullContent.trim(); // Remove trailing newline

    const newUrl = await createTemporaryUrl(fullContent);
    
    const script = `
local success, result = pcall(function()
  return game:HttpGet("${newUrl}")
end)

if success then
  loadstring(result)()
else
  warn("Failed to load script:", result)
end
`;
    
    return new Response(script, {
      headers: { 'Content-Type': 'application/lua' }
    });
  } catch (error) {
    console.error('Error:', error.message);
    return new Response('Acceso denegado', { status: 403 });
  }
}

async function fetchPasteContent(slug) {
  try {
    const response = await fetch(`https://paste-drop.com/raw/${slug}`);
    if (!response.ok) throw new Error(`Failed to fetch content for slug: ${slug}`);
    const htmlContent = await response.text();
    
    const contentMatch = htmlContent.match(/<div class="content">([\s\S]*?)<\/div>/);
    if (!contentMatch || !contentMatch[1]) throw new Error(`Invalid content format for slug: ${slug}`);
    
    return contentMatch[1];
  } catch (error) {
    console.error('Error fetching paste content:', error.message);
    throw error;
  }
}

async function createTemporaryUrl(content) {
  const apiUrl = 'https://api-fhi1.onrender.com/create';
  try {
    const encodedContent = btoa(unescape(encodeURIComponent(content))); // Base64 encode the content
    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ text: encodedContent })
    });

    if (!response.ok) throw new Error('Failed to create temporary URL');

    const data = await response.json();
    if (!data.url) throw new Error('Invalid response from API');

    return `https://api-fhi1.onrender.com${data.url}`;
  } catch (error) {
    console.error('Error creating temporary URL:', error.message);
    throw error;
  }
}
