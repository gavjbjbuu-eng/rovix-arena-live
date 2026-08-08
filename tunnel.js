const localtunnel = require('localtunnel'); (async () => { const tunnel = await localtunnel({ port: 5000 }); console.log('URL: ' + tunnel.url); })();
