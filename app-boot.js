/* =====================================================================
   SOHAG BD SHOP — app-boot.js  (shared page bootstrap + demo API layer)
   ---------------------------------------------------------------------
   Every page loads this file first, inside <head>. It provides:

   1.  window.SBD helpers that the pages already call:
         SBD.requireLogin()            redirect to login.html when signed out
         SBD.ready(fn, opts)           run after DOM ready (+ every page show)
         SBD.poll(fn, ms)              background-tab-safe polling
         SBD.cacheGet / SBD.cacheSet   shared short-lived response cache

   2.  DEMO BACKEND EMULATION.  The original site is backed by PHP APIs
       (api_user_login.php, api_balance.php, api_orders.php …) and a
       Telegram bot that mails the one-time login code.  That backend is
       not part of this repository, so — while this demo flag is on —
       window.fetch() calls to any  api_*.php  endpoint are answered
       locally from localStorage. That makes the whole shop work as a
       self-contained static site (GitHub Pages / any web host), so you
       can click through Login → Deposit → Shop → Orders → Transfer.

       To use the real PHP backend instead: remove/rename this file's
       demo layer or open the site with  ?demo=0  — real requests then
       go straight to the server, exactly as before.

   IMPORTANT: the emulated endpoints mirror the JSON contracts of the
   PHP originals, so switching to the real backend needs no HTML change.
   ===================================================================== */

(function () {
    'use strict';

    /* ------------------------------------------------------------------
       0. Demo switch
       ------------------------------------------------------------------ */
    var DEMO = true;
    try {
        var q = new URLSearchParams(window.location.search);
        if (q.get('demo') === '0') DEMO = false;
        if (q.get('demo') === '1') DEMO = true;
    } catch (e) { /* older browser — keep default */ }
    window.SBD_DEMO = DEMO;   // readable by pages (login demo chip)

    /* ------------------------------------------------------------------
       1. tiny storage helpers (never throw on private mode)
       ------------------------------------------------------------------ */
    var PREFIX = 'sbd:';
    function read(key, fallback) {
        try {
            var raw = localStorage.getItem(PREFIX + key);
            if (!raw) return fallback;
            return JSON.parse(raw);
        } catch (e) { return fallback; }
    }
    function write(key, value) {
        try { localStorage.setItem(PREFIX + key, JSON.stringify(value)); }
        catch (e) { /* storage blocked — demo state just won't persist */ }
    }
    function remove(key) {
        try { localStorage.removeItem(PREFIX + key); } catch (e) {}
    }

    function now() { return Date.now(); }
    function uid(prefix) {
        return (prefix || 'ID') + '-' + now().toString(36).toUpperCase()
             + Math.random().toString(36).slice(2, 6).toUpperCase();
    }
    function pad(n) { return String(n).length < 2 ? '0' + n : String(n); }
    function stamp() {
        var d = new Date();
        return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate())
             + ' ' + pad(d.getHours()) + ':' + pad(d.getMinutes()) + ':' + pad(d.getSeconds());
    }
    function fmtMoney(n) { return '$' + parseFloat(n || 0).toFixed(2); }
    function maskTg(id) {
        var s = String(id == null ? '' : id).replace(/\D+/g, '');
        if (s.length <= 4) return s;
        return '••••' + s.slice(-4);
    }

    /* ------------------------------------------------------------------
       2. Accounts / wallet / deposits / orders / OTP  — demo data store
       ------------------------------------------------------------------ */
    function accounts() { return read('accounts', {}); }               // { tg: {profile.., balance} }
    function deposits() { return read('deposits', []); }               // array, newest last
    function orders()   { return read('orders', []); }                 // array, newest last
    function otps()     { return read('otps', {}); }                   // { challenge: {..} }

    function saveAccounts(v) { write('accounts', v); }
    function saveDeposits(v) { write('deposits', v); }
    function saveOrders(v)   { write('orders', v); }
    function saveOtps(v)     { write('otps', v); }

    /* Recipients that exist so the Fund-Transfer flow can be tried out. */
    function seededUsers() {
        return {
            '8801618202470': { fullName: 'Sohag BD Support', firstName: 'Sohag', lastName: 'BD', username: 'SH_5617' },
            '123456789':     { fullName: 'Demo Buyer',       firstName: 'Demo', lastName: 'Buyer', username: 'demo_buyer' }
        };
    }

    function makeAccount(tg) {
        var seed = seededUsers()[tg];
        var name = seed ? seed.fullName : 'Sohag BD customer';
        return {
            telegramId: String(tg),
            accountId: 'A-' + String(tg),
            fullName: name,
            firstName: seed ? seed.firstName : 'Sohag',
            lastName: seed ? seed.lastName : 'customer',
            username: seed ? seed.username : ('user_' + String(tg)).slice(0, 32),
            joinDate: new Date().toISOString(),
            status: 'active',
            balance: 0
        };
    }

    function getAccount(tg) {
        var list = accounts();
        var acc = list[tg];
        if (!acc) {
            acc = makeAccount(tg);
            list[tg] = acc;
            saveAccounts(list);
        }
        return acc;
    }

    function setBalance(tg, value) {
        var list = accounts();
        var acc = list[tg] || getAccount(tg);
        acc.balance = Math.max(0, Math.round((parseFloat(value) || 0) * 100) / 100);
        list[tg] = acc;
        saveAccounts(list);
        bumpCacheClock();
        return acc.balance;
    }
    function addBalance(tg, delta) {
        var acc = getAccount(tg);
        return setBalance(tg, (parseFloat(acc.balance) || 0) + (parseFloat(delta) || 0));
    }
    function balanceOf(tg) {
        var acc = accounts()[tg];
        return acc ? (parseFloat(acc.balance) || 0) : 0;
    }

    /* ------------------------------------------------------------------
       3. The one-time-code store
       ------------------------------------------------------------------ */
    function newOtp(tg) {
        var code = String(Math.floor(100000 + Math.random() * 900000));
        var store = otps();
        store[tg] = { code: code, expiresAt: now() + 5 * 60 * 1000, resendAt: now() + 60 * 1000 };
        saveOtps(store);
        return store[tg];
    }
    function currentOtp(tg) {
        var store = otps();
        var o = store[tg];
        if (!o) return null;
        if (now() > o.expiresAt) { delete store[tg]; saveOtps(store); return null; }
        return o;
    }

    /* ------------------------------------------------------------------
       4. Simulated "admin" — auto-approves deposits and completes orders
          a few seconds after they are submitted, so the Pending pages
          come alive on their own.
       ------------------------------------------------------------------ */
    function notifyStore() {
        try {
            localStorage.setItem('sbd:event', String(now()));   // cross-tab heads-up
            localStorage.setItem('deposit_updated', String(now()));
        } catch (e) {}
    }
    function scheduleDepositApproval(tg, usd, id) {
        setTimeout(function () {
            var list = deposits();
            var dep = null;
            for (var i = 0; i < list.length; i++) {
                if (String(list[i].id) === String(id)) { dep = list[i]; break; }
            }
            if (!dep || dep.status !== 'Pending') return;
            dep.status = 'Approved';
            saveDeposits(list);
            addBalance(tg, usd);
            notifyStore();
        }, 12000);
    }
    function scheduleOrderCompletion(orderId) {
        setTimeout(function () {
            var list = orders();
            var order = null;
            for (var i = 0; i < list.length; i++) {
                if (String(list[i].order_id) === String(orderId)) { order = list[i]; break; }
            }
            if (!order || order.status !== 'Pending') return;
            order.status = 'Completed';
            var lines = ['Your order has been delivered automatically.'];
            if (order.download_url) lines.push('Download File: ' + order.download_url);
            lines = lines.concat([
                '',
                'Product key: BRDX-' + rk4() + '-' + rk4() + '-' + rk4(),
                'Backup key:   BRDX-' + rk4() + '-' + rk4() + '-' + rk4(),
                '',
                'Thank you for shopping with SOHAG BD SHOP!'
            ]);
            order.delivery_data = lines.join('\n');
            saveOrders(list);
            notifyStore();
        }, 9000);
    }
    function rk4() {
        var chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ0123456789';
        var s = '';
        for (var i = 0; i < 4; i++) s += chars.charAt(Math.floor(Math.random() * chars.length));
        return s;
    }

    /* ------------------------------------------------------------------
       5. Shared response cache (pages read it through SBD.cacheGet/Set)
       ------------------------------------------------------------------ */
    var memCache = {};
    function bumpCacheClock() { memCache = {}; }   // wallet changes invalidate warm cache

    function cacheSet(key, data, ttl) {
        var k = 'sbd:cache:' + key;
        memCache[key] = { data: data, exp: now() + (parseInt(ttl, 10) || 300000) };
        try { localStorage.setItem(k, JSON.stringify(memCache[key])); } catch (e) {}
    }
    function cacheGet(key) {
        var hit = memCache[key];
        if (!hit) {
            try {
                var raw = localStorage.getItem('sbd:cache:' + key);
                if (raw) hit = JSON.parse(raw);
            } catch (e) { hit = null; }
        }
        if (!hit || !hit.data) return null;
        if (now() > hit.exp) return null;           // expired — ignore
        return hit.data;
    }

    /* ------------------------------------------------------------------
       6. API emulation  —  every api_*.php call the pages make
       ------------------------------------------------------------------ */
    var USER_SESSION_KEY = 'sessionTg';

    function sessionTg() {
        try {
            var stored = read(USER_SESSION_KEY, null);
            if (stored) return String(stored);
        } catch (e) {}
        // Fall back to the client flags other pages write after a verify_otp
        try {
            if (localStorage.getItem('isLoggedIn') === 'true') {
                var tg = localStorage.getItem('userTelegramId');
                if (tg) return tg;
            }
        } catch (e) {}
        return null;
    }

    function res(data, status) {
        status = status || 200;
        return {
            ok: status >= 200 && status < 300,
            status: status,
            json: function () { return Promise.resolve(data); },
            text: function () { return Promise.resolve(JSON.stringify(data)); }
        };
    }

    function randomChallenge() {
        return 'ch_' + now().toString(36) + Math.random().toString(36).slice(2, 10);
    }

    /* Each route returns {status, body} */
    function routeApi(path, params, body) {
        var name = String(path || '').split('?')[0].split('/').pop();
        var action = (params && params.get ? params.get('action') : null) || (body && body.action) || '';

        switch (name) {

        /* ---------- api_user_login.php ---------- */
        case 'api_user_login.php': {
            if (action === 'config') {
                return { body: {
                    success: true, length: 6, ttl: 300, resend_in: 60,
                    bot: 'SBSHOPNOTIFY_BOT', bot_url: 'https://t.me/SBSHOPNOTIFY_BOT'
                } };
            }
            if (action === 'session') {
                var tg = sessionTg();
                if (!tg) return { body: { logged_in: false } };
                var acc = getAccount(tg);
                return { body: {
                    logged_in: true, telegram_id: tg,
                    account: { full_name: acc.fullName, telegram_username: acc.username,
                               first_name: acc.firstName, status: acc.status, balance: acc.balance }
                } };
            }
            if (action === 'logout') {
                remove(USER_SESSION_KEY);
                return { body: { success: true } };
            }
            if (action === 'request_otp' || action === 'resend_otp') {
                var tgId = String((body && body.telegram_id != null) ? body.telegram_id : '')
                              .replace(/\D+/g, '');
                if (!tgId) return { body: { success: false, message: 'Please enter your Telegram ID.' } };
                if (tgId.length < 5) {
                    return { body: { success: false, message: "That doesn't look like a Telegram ID.",
                                     reason: 'not_found', retry_after: 0 } };
                }
                var acc = getAccount(tgId);
                var existing = currentOtp(tgId);
                if (action === 'request_otp' && existing) {
                    // A fresh code was already sent moments ago — reuse it
                    var ch = randomChallenge();
                    var store = otps();
                    store[tgId] = existing;   // keep timing
                    store[ch] = { code: existing.code, expiresAt: existing.expiresAt, resendAt: existing.resendAt, tg: tgId };
                    saveOtps(store);
                    return { body: {
                        success: true, reused: true, challenge: ch, length: 6, ttl: 300, resend_in: 60,
                        name: acc.fullName, tg_masked: maskTg(tgId),
                        demo_code: DEMO ? existing.code : undefined,
                        expires_in: Math.max(0, Math.round((existing.expiresAt - now()) / 1000)),
                        resend_in_actual: Math.max(0, Math.round((existing.resendAt - now()) / 1000))
                    } };
                }
                var otp = newOtp(tgId);
                var challenge = randomChallenge();
                store = otps();
                store[challenge] = { code: otp.code, expiresAt: otp.expiresAt, resendAt: otp.resendAt, tg: tgId };
                saveOtps(store);
                return { body: {
                    success: true, reused: false, challenge: challenge, length: 6, ttl: 300, resend_in: 60,
                    name: acc.fullName, tg_masked: maskTg(tgId),
                    demo_code: DEMO ? otp.code : undefined,
                    expires_in: 300, resend_in: 60
                } };
            }
            if (action === 'verify_otp') {
                var ch2 = body && body.challenge;
                var code2 = String((body && body.code) || '').replace(/\D+/g, '');
                var store2 = otps();
                var entry = ch2 && store2[ch2];
                if (!entry || now() > entry.expiresAt) {
                    return { body: { success: false, message: 'This code has expired. Tap Resend to get a new one.', reason: 'expired' } };
                }
                if (entry.used) {
                    return { body: { success: false, message: 'This code was already used. Please request a new one.', reason: 'used' } };
                }
                if (entry.code !== code2) {
                    return { body: { success: false, message: 'Wrong code. Please re-check the code sent to your Telegram.', reason: 'wrong_code' } };
                }
                entry.used = true;
                saveOtps(store2);
                var userTg = entry.tg;
                var acc2 = getAccount(userTg);
                write(USER_SESSION_KEY, userTg);
                return { body: {
                    success: true,
                    user: {
                        chat_id: userTg,
                        account_id: acc2.accountId,
                        username: acc2.username,
                        first_name: acc2.firstName,
                        last_name: acc2.lastName,
                        full_name: acc2.fullName,
                        status: acc2.status
                    }
                } };
            }
            return { body: { success: false, message: 'Unknown action.' } };
        }

        /* ---------- api_balance.php ---------- */
        case 'api_balance.php': {
            var tgBal = (params && params.get ? params.get('telegram_id') : '') || (body && body.telegram_id) || '';
            if (!tgBal) return { body: { success: false } };
            return { body: { success: true, balance: balanceOf(String(tgBal).replace(/\D+/g, '')) } };
        }

        /* ---------- api_check_block.php ---------- */
        case 'api_check_block.php': {
            var tgBlk = (params && params.get ? params.get('telegram_id') : '') || '';
            var accBlk = accounts()[String(tgBlk).replace(/\D+/g, '')];
            if (accBlk && accBlk.status === 'banned') {
                return { body: { blocked: true, permanent: true, reason: accBlk.ban_reason || 'Violation of terms' } };
            }
            return { body: { blocked: false } };
        }

        /* ---------- api_users.php ---------- */
        case 'api_users.php': {
            var tgU = (params && params.get ? params.get('telegram_id') : '') || '';
            var accU = accounts()[String(tgU).replace(/\D+/g, '')];
            if (!accU) return { body: { success: false, message: 'User not found.' } };
            return { body: { success: true, user: {
                id: accU.accountId, telegram_id: accU.telegramId,
                full_name: accU.fullName, username: accU.username,
                status: accU.status, join_date: accU.joinDate, balance: accU.balance
            } } };
        }

        /* ---------- api_tg_profile.php ---------- */
        case 'api_tg_profile.php': {
            var ses = sessionTg();
            if (!ses) return { status: 403, body: { success: false, message: 'No session.' } };
            var a = getAccount(ses);
            return { body: {
                success: true,
                first_name: a.firstName, last_name: a.lastName,
                username: a.username, full_name: a.fullName
            } };
        }

        /* ---------- api_save_deposit.php ---------- */
        case 'api_save_deposit.php': {
            var depBody = body || {};
            var method = depBody.method || 'bKash';
            var usd = parseFloat(depBody.usdAmount) || 0;
            var amountLabel = depBody.amount || ('$' + usd.toFixed(2));
            var depId = 'D' + String(Math.floor(100000 + Math.random() * 900000));
            var depList = deposits();
            depList.push({
                id: depId,
                telegram_id: String(depBody.userTelegramId || '').replace(/\D+/g, ''),
                method: method,
                amount: amountLabel,
                usdAmount: usd,
                trxid: depBody.trx || ('TRX' + Math.random().toString(36).slice(2, 8).toUpperCase()),
                status: 'Pending',
                created_at: stamp(),
                admin_note: ''
            });
            saveDeposits(depList);
            scheduleDepositApproval(depList[depList.length - 1].telegram_id, usd, depId);
            return { body: {
                ok: true, id: depId, trxid: depBody.trx, status: 'Pending', created_at: stamp()
            } };
        }

        /* ---------- api_user_deposits.php ---------- */
        case 'api_user_deposits.php': {
            var whoBody = body || {};
            var who = whoBody.user_id || whoBody.email || '';
            var out = deposits().filter(function (d) {
                return String(d.telegram_id) === String(who).replace(/\D+/g, '');
            });
            return { body: out.reverse() };   // newest first — matches the page's loop order
        }

        /* ---------- api_orders.php ---------- */
        case 'api_orders.php': {
            if (action === 'user_list') {
                var tgO = (params && params.get ? params.get('telegram_id') : '') || '';
                var mine = orders().filter(function (o) {
                    return String(o.telegram_id) === String(tgO).replace(/\D+/g, '');
                });
                return { body: { success: true, orders: mine } };
            }
            return { body: { success: false, orders: [] } };
        }

        /* ---------- api_place_order.php  (used by shop.html) ---------- */
        case 'api_place_order.php': {
            var ob = body || {};
            var buyer = String(ob.telegram_id || '').replace(/\D+/g, '');
            var price = parseFloat(ob.price) || 0;
            var qty = parseInt(ob.quantity, 10) || 1;
            if (!buyer) return { body: { success: false, message: 'Please login first.' } };
            if (price * qty <= 0) return { body: { success: false, message: 'Invalid price.' } };
            var bal = balanceOf(buyer);
            if (bal < price * qty - 0.0001) {
                return { body: { success: false, message: 'Insufficient balance. Please deposit first.', reason: 'insufficient' } };
            }
            var orderId = 'SB' + Math.floor(100000 + Math.random() * 900000);
            var o = {
                order_id: orderId,
                telegram_id: buyer,
                title: ob.title || 'Digital Product',
                details: ob.details || '',
                price: price,
                quantity: qty,
                date: new Date().toISOString(),
                status: 'Pending',
                download_url: ob.download_url || '',
                delivery_data: null
            };
            var all = orders();
            all.push(o);
            saveOrders(all);
            setBalance(buyer, bal - price * qty);
            scheduleOrderCompletion(orderId);
            return { body: { success: true, order: o, balance: balanceOf(buyer) } };
        }

        /* ---------- api_fund_transfer.php ---------- */
        case 'api_fund_transfer.php': {
            var from = sessionTg();
            if (!from) return { body: { success: false, reason: 'auth', message: 'Please login again.', relogin: true } };
            var fb = body || {};
            if (action === 'info' || action === '' || action === 'history') {
                var balF = balanceOf(from);
                return { body: {
                    success: true, fee: 0.02, fee_per_block: 0.02, fee_block: 1.00,
                    min: 0.03, max: 5000, min_credit: 0.01,
                    balance: balF, max_sendable: Math.max(0, balF),
                    can_send: balF >= 0.03, blocked: false
                } };
            }
            if (action === 'lookup') {
                var rid = String(fb.recipient_id || '').replace(/\D+/g, '');
                var target = accounts()[rid] || seededUsers()[rid];
                if (!target) {
                    return { body: { success: false, found: false, message: 'Account not found. Check the User ID and try again.', reason: 'not_found' } };
                }
                var tn = target.fullName || target.full_name || ('User ' + rid);
                return { body: { success: true, found: true, name: tn, username: target.username || '' } };
            }
            if (action === 'transfer') {
                var rid2 = String(fb.recipient_id || '').replace(/\D+/g, '');
                var amt = Math.max(0, parseFloat(fb.amount) || 0);
                var tar = accounts()[rid2] || seededUsers()[rid2];
                if (!tar) {
                    return { body: { success: false, reason: 'not_found', message: 'Account not found.' } };
                }
                var balS = balanceOf(from);
                var fee = amt >= 1 ? 0.02 : 0;      // $0.02 flat per the deposit page copy
                var net = Math.max(0, Math.round((amt - fee) * 100) / 100);
                if (amt > balS + 0.0001) {
                    return { body: { success: false, message: 'Insufficient balance.' } };
                }
                setBalance(from, balS - amt);
                // Credit the recipient (create the account when it does not exist yet)
                var listT = accounts();
                if (!listT[rid2]) listT[rid2] = makeAccount(rid2);
                listT[rid2].balance = Math.round(((parseFloat(listT[rid2].balance) || 0) + net) * 100) / 100;
                saveAccounts(listT);
                bumpCacheClock();
                var accT = listT[rid2];
                var tId = 'T' + Math.floor(100000 + Math.random() * 900000);
                return { body: {
                    success: true, id: tId, amount: amt, fee: fee, net: net,
                    balance: balanceOf(from), to_name: accT.fullName,
                    to_id: rid2, to_username: accT.username,
                    date: new Date().toISOString().replace('T', ' ').slice(0, 19)
                } };
            }
            return { body: { success: false, message: 'Unknown transfer action.' } };
        }

        default:
            return { status: 404, body: { success: false, message: 'Endpoint not emulated: ' + name } };
        }
    }

    /* ------------------------------------------------------------------
       7. fetch() wrapper — only used while DEMO is on.
          Real (non api_*.php) requests always go out to the network.
       ------------------------------------------------------------------ */
    function installDemoFetch() {
        var nativeFetch = window.fetch ? window.fetch.bind(window) : null;
        if (!nativeFetch) return;

        window.fetch = function (input, init) {
            var url = typeof input === 'string' ? input : (input && input.url) || '';
            var method = ((init && init.method) || (input && input.method) || 'GET').toUpperCase();

            // Route only same-origin calls to api_*.php
            try {
                var parsed = new URL(url, window.location.href);
                var isApi = /^api_[a-z0-9_]+\.php$/i.test(parsed.pathname.split('/').pop());
                if (!isApi) return nativeFetch(input, init);

                var params = new URLSearchParams(parsed.search);

                var bodyPromise = Promise.resolve(null);
                if (init && init.body) {
                    var rawBody = init.body;
                    bodyPromise = (typeof rawBody === 'string')
                        ? Promise.resolve(rawBody)
                        : rawBody.text().catch(function () { return null; });
                }

                return bodyPromise.then(function (raw) {
                    var body = null;
                    if (raw) {
                        try { body = JSON.parse(raw); }
                        catch (e) { body = { _raw: raw }; }
                    }
                    var out = routeApi(parsed.pathname, params, body);
                    return res(out.body, out.status || 200);
                });
            } catch (e) {
                return nativeFetch(input, init);
            }
        };
    }

    /* ------------------------------------------------------------------
       8. SBD helper object  —  the API the pages already use
       ------------------------------------------------------------------ */
    function requireLogin() {
        try {
            if (localStorage.getItem('isLoggedIn') !== 'true') {
                window.location.replace('login.html');
                return false;
            }
        } catch (e) { window.location.replace('login.html'); return false; }
        return true;
    }

    function ready(fn, opts) {
        opts = opts || {};
        function run() { if (typeof fn === 'function') fn(); }
        function onReady() {
            if (!DEMO && opts.onEveryShow && typeof window.addEventListener === 'function') {
                window.addEventListener('pageshow', function () {
                    setTimeout(run, 0);
                });
            }
            run();
        }
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', onReady);
        } else {
            setTimeout(onReady, 0);
        }
    }

    function poll(fn, interval) {
        if (typeof fn !== 'function') return;
        var tick = function () {
            if (document.hidden) return;      // background tab → skip
            try { fn(); } catch (e) {}
        };
        setInterval(tick, Math.max(3000, parseInt(interval, 10) || 15000));
    }

    var SBD = {
        requireLogin: requireLogin,
        ready: ready,
        poll: poll,
        cacheGet: cacheGet,
        cacheSet: cacheSet,
        demo: DEMO,
        version: 4
    };
    window.SBD = SBD;

    /* Expose helpers the demo pages (shop.html) also use */
    window.SBDHelpers = {
        getAccount: getAccount,
        balanceOf: balanceOf,
        fmtMoney: fmtMoney,
        uid: uid
    };

    if (DEMO) installDemoFetch();
})();
