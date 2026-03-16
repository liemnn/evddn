odoo.define('my_pwa.register_sw', function (require) {
    "use strict";

    // chỉ chạy trên client public website
    if ('serviceWorker' in navigator) {
        window.addEventListener('load', function() {
            // đường dẫn tới service worker file
            navigator.serviceWorker.register('/my_pwa/static/serviceworker.js')
            .then(function(registration) {
                console.log('ServiceWorker registered with scope:', registration.scope);
            }).catch(function(err){
                console.warn('ServiceWorker registration failed:', err);
            });
        });
    }
});
