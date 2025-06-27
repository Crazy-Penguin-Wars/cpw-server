var _____WB$wombat$assign$function_____ = function(name) {return (self._wb_wombat && self._wb_wombat.local_init && self._wb_wombat.local_init(name)) || self[name]; };
if (!self.__WB_pmw) { self.__WB_pmw = function(obj) { this.__WB_source = obj; return this; } }
{
  let window = _____WB$wombat$assign$function_____("window");
  let self = _____WB$wombat$assign$function_____("self");
  let document = _____WB$wombat$assign$function_____("document");
  let location = _____WB$wombat$assign$function_____("location");
  let top = _____WB$wombat$assign$function_____("top");
  let parent = _____WB$wombat$assign$function_____("parent");
  let frames = _____WB$wombat$assign$function_____("frames");
  let opener = _____WB$wombat$assign$function_____("opener");

var PaymentClient = (function(window) {

    var MessageBroker = {

        wasCalledRecently: {},

        receive: function(event, instance) {
            var message = this.extract(event.data);

            if (message) {
                return this.execute(message, instance);
            }

            return message;
        },

        extract: function(data) {
            var message = false;

            try {
                message = JSON.parse(data);
            } catch (ex) {
                message = false;
            }

            return message;
        },

        execute: function(message, instance) {
            var method = message.method;

            if ('string' === typeof method) {
                if (this.wasCalledRecently[method]) {
                    return false;
                }

                var onMethod = 'on' + method.charAt(0).toUpperCase() + method.substr(1);

                if ('function' === typeof instance[onMethod]) {
                    instance[onMethod].call(instance, message.parameters);
                    this.mark(method);
                    return message;
                }
            }

            return false;
        },

        mark: function(method) {
            var self = this;

            this.wasCalledRecently[method] = true;

            window.setTimeout(function() {
                self.wasCalledRecently[method] = false;
            }, 1500);
        },

        send: function(message) {
            try {
                window.parent.postMessage(JSON.stringify(message), '*');
            } catch (ex) {}

            try {
                window.top.postMessage(JSON.stringify(message), '*');
            } catch (ex) {}

            try {
                window.self.postMessage(JSON.stringify(message), '*');
            } catch (ex) {}
        }
    };

    function PublicInterface() {
        var self = this;

        /* Enables access to the specific instance (self) from the MessageBroker */
        var BrokerProxy = function(event) {
            MessageBroker.receive(event, self);
        };

        if (window.addEventListener) {
            window.addEventListener('message', BrokerProxy, false);
        } else if (window.attachEvent) {
            window.attachEvent('onmessage', BrokerProxy);
        }

        this.checkLocationHash = function(location) {
            var data = false;
            var hash = '';

            try {
                hash = location.hash.substring(1);
            } catch (ex) {
                return false;
            }

            /* Simple trigger, no promotion attached */
            if ('trigger-payment-window' === hash) {
                try {
                    location.hash = '';
                } catch (ex) {}

                return true;
            }

            /* Not a simple trigger, check if it is JSON */
            try {
                data = JSON.parse(hash);
            } catch (ex) {
                data = false;
            }

            if (false === data) {
                return false;
            }

            /* Check if Object from JSON contains positive multiplier property */
            if (parseFloat(data.multiplier) > 1.0) {
                this.onOpen = function() {
                    this.showPromotion(data);
                };

                try {
                    location.hash = '';
                } catch (ex) {}

                return true;
            }

            return false;
        };
    }

    PublicInterface.prototype = {

        /**
         * Show payment window
         *
         * Sends the given key-value object to the portal script. The portal script in turn will
         * trigger the payment window with the given key-value parameters.
         *
         * @param {Object} parameters
         *
         * @access public
         */
        showPaymentSelectionScreen: function(parameters) {
            var message = {
                'method': 'showPaymentOptions',
                'parameters': parameters
            };

            MessageBroker.send(message);
        },

        /**
         * Show offer window.
         *
         * This is a terrible and ugly prototype implementation and should be
         * refactored if the test phase proves the functionality of it is useful.
         *
         * @param {Object} parameters
         *
         * @access public
         */
        showOfferWindow: function(parameters) {

            /*
            var parameters = {
                gameId: "112",
                params: "accountId=19",
                siteId: 79,
                token: "a759d180-9c59-11e2-abe3-90b8d01edb3a",
                userId: "jordidchoc",
                sku: "Coins"
            };
            */

            var div = document.getElementById('offer-window-div');
            var iframe = document.getElementById('offer-window-iframe');
            if (div || iframe) {
                return;
            }

            var defaults = {
                'domain': 'https://web.archive.org/web/20140328025959/https://payments.spilgames.com',
                'resolve': true,
                'pattern': new RegExp('^(https?:\/\/[^\/]+)\/.+(payment.portal|payment.client).js', 'i'),
                'page': '/matomy/'
            };

            function mergeRecursive(base, merge, discardUnmatched) {
                for (var key in merge) {
                    if (true === merge.hasOwnProperty(key)) {
                        try {
                            if (false === base.hasOwnProperty(key) && true === discardUnmatched) {
                                continue;
                            }
                            if (Object === merge[key].constructor) {
                                base[key] = mergeRecursive(base[key], merge[key], discardUnmatched);
                            } else {
                                base[key] = merge[key];
                            }
                        } catch(e) {
                            base[key] = merge[key];
                        }
                    }
                }
                return base;
            }

            function resolveDomain() {
                var domain = defaults.domain;
                if (defaults.resolve) {
                    var pattern = defaults.pattern;
                    var scripts = document.getElementsByTagName('script');
                    var length = scripts.length;
                    for (var iterator = 0; iterator < length; iterator++) {
                        var matches = pattern.exec(scripts[iterator].src);
                        if (matches && matches.length > 1) {
                            domain = matches[1];
                        }
                    }
                }
                return domain;
            }

            var keys = {
                'game_id': parameters.gameId,
                'site_id': parameters.siteId,
                'user_id': parameters.userId,
                'transaction_token': parameters.token,
                'sku_type': 'Galaxy Chips',
                'internal_sku_name': 'digichocochips',
                'extra_params': parameters.params
            };

            var encoded = '';
            for (var key in keys) {
                if (keys.hasOwnProperty(key)) {
                    encoded += encoded.length > 0 ? '&' : '?';
                    encoded += key + '=' + encodeURIComponent(keys[key]);
                }
            }

            var body = document.getElementsByTagName('body')[0];

            iframe = document.createElement('iframe');

            iframe.setAttribute('id', 'offer-window-iframe');
            iframe.setAttribute('height', '100%');
            iframe.setAttribute('width', '100%');
            iframe.setAttribute('border', 0);
            iframe.setAttribute('frameBorder', 0);
            iframe.setAttribute('allowTransparency', 'true');
            iframe.setAttribute('vspace', 0);
            iframe.setAttribute('hspace', 0);
            iframe.setAttribute('src', resolveDomain() + defaults.page + encoded);

            var istyles = {
                backgroundColor: '#FFFFFF',
                position: 'fixed',
                top: '15px',
                left: 0,
                zIndex: 999999
            };

            mergeRecursive(iframe.style, istyles, false);

            div = document.createElement('div');

            div.setAttribute('id', 'offer-window-div');

            var dstyles = {
                top: 0,
                left: 0,
                backgroundColor: '#000000',
                height: '15px',
                width: '100%',
                position: 'fixed',
                textAlign: 'center',
                zIndex: 999999
            };

            mergeRecursive(div.style, dstyles, false);

            var paragraph = document.createElement('p');

            paragraph.innerHTML = 'CLICK TO CLOSE';

            var pstyles = {
                position: 'relative',
                top: 0,
                left: 0,
                height: '15px',
                color: 'white'
            };

            mergeRecursive(paragraph.style, pstyles, false);

            div.appendChild(paragraph);

            div.onclick = function() {
                body.removeChild(div);
                body.removeChild(iframe);
            };

            body.appendChild(div);
            body.appendChild(iframe);
        },

        /**
         * Check instant-trigger status
         *
         * Given that a user visits agame.com/gamepage.html#trigger-payment-window - this function
         * will return true when called. This indicates that the third party developer should immediately
         * open the payment window for the user. The domain and gamepage in this example are fictional,
         * but the hash string should be exactly that.
         *
         * @return {Boolean}
         *
         * @access public
         */
        hasExternalTrigger: function() {
            var curWindow = this.checkLocationHash(window.location);
            var topWindow = this.checkLocationHash(window.top.location);

            return curWindow || topWindow;
        },

        /**
         * Show a promotion
         *
         * @param {Object} parameters
         *
         * @access public
         */
        showPromotion: function(parameters) {
            var message = {
                'method': 'promotion',
                'parameters': parameters
            };

            if (parseFloat(message.parameters.multiplier) > 1.0) {
                MessageBroker.send(message);
            }
        }

    };

    return PublicInterface;

}(window));


}
/*
     FILE ARCHIVED ON 02:59:59 Mar 28, 2014 AND RETRIEVED FROM THE
     INTERNET ARCHIVE ON 13:47:22 Jul 29, 2022.
     JAVASCRIPT APPENDED BY WAYBACK MACHINE, COPYRIGHT INTERNET ARCHIVE.

     ALL OTHER CONTENT MAY ALSO BE PROTECTED BY COPYRIGHT (17 U.S.C.
     SECTION 108(a)(3)).
*/
/*
playback timings (ms):
  captures_list: 329.611
  exclusion.robots: 97.472
  exclusion.robots.policy: 97.46
  xauthn.identify: 64.315
  xauthn.chkprivs: 32.844
  RedisCDXSource: 0.758
  esindex: 0.01
  LoadShardBlock: 175.583 (3)
  PetaboxLoader3.datanode: 135.843 (5)
  CDXLines.iter: 32.786 (3)
  load_resource: 229.151 (2)
  PetaboxLoader3.resolve: 77.031 (2)
*/