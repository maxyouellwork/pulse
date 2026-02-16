// worker.js
var worker_default = {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    if (url.pathname.startsWith("/englands-pothole-crisis")) {
      const newPath = url.pathname.replace("/englands-pothole-crisis", "/englands-pothole-problem");
      return Response.redirect(`https://projects.maxyouell.co.uk${newPath}`, 301);
    }
    if (url.pathname === "/englands-pothole-problem") {
      return Response.redirect(`https://projects.maxyouell.co.uk/englands-pothole-problem/`, 301);
    }
    if (url.pathname.startsWith("/englands-pothole-problem/")) {
      const targetUrl = new URL(request.url);
      targetUrl.hostname = "englands-pothole-problem.pages.dev";
      targetUrl.pathname = url.pathname.replace("/englands-pothole-problem", "") || "/";
      return fetch(targetUrl, request);
    }
    if (url.pathname.startsWith("/on-the-agenda")) {
      const targetUrl = new URL(request.url);
      targetUrl.protocol = "http:";
      targetUrl.hostname = "agenda-render.maxyouell.co.uk";
      targetUrl.port = "3000";
      return fetch(targetUrl.toString(), {
        method: request.method,
        headers: request.headers,
        body: request.body
      });
    }
    if (url.pathname.startsWith("/cocktails")) {
      const targetUrl = new URL(request.url);
      targetUrl.hostname = "cocktails-now.pages.dev";
      return fetch(targetUrl, request);
    }
    if (url.pathname === "/pint-price-index") {
      return Response.redirect(`https://projects.maxyouell.co.uk/pint-price-index/`, 301);
    }
    if (url.pathname.startsWith("/pint-price-index/")) {
      const targetUrl = new URL(request.url);
      targetUrl.hostname = "pint-price-index.pages.dev";
      targetUrl.pathname = url.pathname.replace("/pint-price-index", "") || "/";
      return fetch(targetUrl, request);
    }
    if (url.pathname === "/" || url.pathname === "") {
      return new Response(`<!DOCTYPE html>
<html>
<head>
  <title>Max Youell - Projects</title>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #fafaf8; color: #1a1a18; padding: 2rem; max-width: 800px; margin: 0 auto; }
    h1 { font-size: 2rem; margin-bottom: 2rem; font-weight: 600; }
    .project { background: white; border-radius: 12px; padding: 1.5rem; margin-bottom: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
    .project h2 { font-size: 1.25rem; margin-bottom: 0.5rem; }
    .project h2 a { color: #d4a574; text-decoration: none; }
    .project h2 a:hover { text-decoration: underline; }
    .project p { color: #666; font-size: 0.95rem; }
  </style>
</head>
<body>
  <h1>Max Youell - Projects</h1>

  <div class="project">
    <h2><a href="/englands-pothole-problem/">England's Pothole Problem</a></h2>
    <p>Interactive visualization of pothole reports across England</p>
  </div>

  <div class="project">
    <h2><a href="/on-the-agenda">On the Agenda</a></h2>
    <p>Turn council meetings into shareable video content</p>
  </div>

  <div class="project">
    <h2><a href="/cocktails">Cocktails, Now</a></h2>
    <p>Find great cocktails near you in Huddersfield</p>
  </div>

  <div class="project">
    <h2><a href="/pint-price-index/">Pint Price Index</a></h2>
    <p>Bloomberg-style terminal tracking pint prices across 778 Wetherspoons pubs</p>
  </div>
</body>
</html>`, {
        headers: { "Content-Type": "text/html;charset=UTF-8" }
      });
    }
    return new Response("Not Found", { status: 404 });
  }
};
var worker_default2 = worker_default;
export {
  worker_default2 as default
};
//# sourceMappingURL=worker.js.map
