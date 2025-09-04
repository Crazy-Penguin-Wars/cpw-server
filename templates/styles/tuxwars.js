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

function canvasReady() {
    //This can be a different platform, so just in case avoid JS exceptions
    try {
	    FB.Canvas.setAutoGrow();
    } catch (ex) {
        //Console.write("Exception caught: " + ex.toString());
    }
}

//Bindings
function createBindings() {
	
	//AJAX calls from links
	$('a.ajax, .ajax a').click(function(event) {
		
		//Prevent default navigation
		event.preventDefault();
		
		//Send request to specified URL
		callServer($(this).attr('href'));
		
	});
	
	//AJAX calls from forms
	$('form.ajax, .ajax form').submit(function(event) {
		
		//Prevent default navigation
		event.preventDefault();
		
		//Send request to specified URL
		callServer($('.url', this).attr('value'));
		
	});
}

function showFlash(h1) {
	$('#play').css({ height : h1 });
}

function commonInit() {
	var commonApiParameters = {
		dcgid : dcgId
	};

    commonApiParameters["maltaAvailable"] = maltaAvailable;
	if (maltaAvailable) {
		commonApiParameters["maltaUserId"] = maltaId;
		commonApiParameters["maltaServer"] = maltaServer;
		commonApiParameters["maltaToken"] = maltaToken;
	}

    commonApiParameters['canvasUrl'] = canvasUrl;
    commonApiParameters['publishCanvasUrl'] = publishCanvasUrl;
    commonApiParameters['platformUserId'] = platformUserId;
    commonApiParameters['currencyCoinsId'] = currencyCoinsId;
    commonApiParameters['currencyPremiumId'] = currencyPremiumId;
    commonApiParameters['federalGameId'] = federalGameId;
    commonApiParameters['serverUrl'] = serverUrl;
    
    
    var platformParameters = {
    		guest : guest,
    		siteId: siteId,
    		channelId: channelId,
    		userId: userId,
    		gameId: gameId,
    		dcgId: dcgId
    };
    

	var commonApi = new CommonApi(commonApiParameters, platformParameters);
	
	return commonApi;
}

function runFlash() {
	var flashVars = {
        uid: dcgId,
        token: token,
        language: language,
        data: assetPath,
        server: serverUrl,
        env: env,
        platform: platform,
        platformServerUrl: platformServerUrl,
	    version: version,
        secure: secure,
        platformUserId: platformUserId
	};

	var params = {
		menu: "true",
        scale: "exactfit",
		quality: "high",
		base: assetPath,
		wmode: "direct",
		id: "GameMovie",
		bgcolor: "#fff",
		allowScriptAccess: "always",
		allowFullScreen: "true"
	};

	var attributes = {};
	
	var rnd = '';
	console.log(devEnv);
	if (devEnv) {
		rnd = '?r='+Math.random();
	}
	swfobject.embedSWF("http://127.0.0.1:5055/assets/GameLauncher.swf"+rnd, "flash", "100%", "668", requiredFlashVersion, false, flashVars, params, attributes);
	jQuery(document).ready(function(){
	    if(!swfobject.hasFlashPlayerVersion(requiredFlashVersion)){
	    	jQuery("#flash").show();
	    }
	});
}

//Reload the whole page
reloadGame = function() {
	
	//Find out the url to the current location
	//FLAG unreliable
	self.parent.location.href = $('#tabs a#tab_' + current_id).attr('href');
	
};

//Send JS command to server
//FLAG always reloads on success
callServer = function(address) {
	
	//Send command as JSON
	$.getJSON(address, function(data){
		
		//Treat response
		if (data.responseCode) {
			
			//Print debug information
			if (debug) {
				if (responseMessage) {
					alert(data.responseCode + "\n\n" + responseMessage);
				} else {
					alert(data.responseCode);
				}
			}
			
		} else {
			
			//Refresh page
			reloadGame();
			
		}
		
	});
};

//Dump parsed JSON data as HTML
function dump(data){
  if(data.constructor == Array ||
     data.constructor == Object){
    document.write('<ul>');
    for(var p in data){
      if(data[p].constructor == Array||
         data[p].constructor == Object){
document.write('<li>[' + p + '] => ' + typeof(data) + '</li>');
        document.write('<ul>');
        dump(data[p]);
        document.write('</ul>');
      } else {
document.write('<li>[' + p + '] => ' + data[p] + '</li>');
      }
    }
    document.write('</ul>');
  }
}

function fromFlash(callType, data) {
	if (callType == "facebookBuyWithCredits") {
		facebookBuyWithCredits(data);
	} else if (callType == "placeOrder") {
		placeOrder(data);
	} else if (callType == "platformPublishFeed") {
		platformPublishFeed(data);
	} else if (callType == "platformSendRequest") {
		platformSendRequest(data);
	} else if (callType == "reload") {
		reload();
	} else if (callType == "crmTrackEvent") {
        crmTrackEventByData(data);
	} else if (callType == "showPaymentUI") {
        showPaymentsUi(data);
	} else if (callType == "showEarnPage") {
        showEarnPage(data);
    }else
	{
		if (debug) {
			alert("Unknown call: " + callType);
		}
	}
}

function toFlash(callType, data) {
	var thisMovie = null;
    if (navigator.appName.indexOf("Microsoft") != -1) {
    	thisMovie = window["flash"];
    } else {
    	thisMovie = document["flash"];
    }
    thisMovie.fromJavascript(callType, data);
}

function calculateSignature(params) {
	return "dummysignature";
}

function reload() {
	window.location.reload();
}

function platformPublishFeed(data) {
    var json = jQuery.parseJSON(data);
    
    var obj = {
		method : 'feed',
		title : json.name,
		link : json.link,
		picture : json.picture,
		caption : json.caption,
		description : json.description,
		actions : JSON.stringify(json.actions),
		product : json.product,
		ref_p_id : json.ref_p_id,
		ref_p_uid : json.ref_p_uid,
		ref_app_id : json.ref_app_id,
		ref_app_uid : json.ref_app_uid,
		feedproperties : json.feedproperties
    };
	if (json.to != null) {
		obj.to = json.to;
	}
	
	// G+
	obj.googleplusTitle = 'Send a post';
	obj.googleplusAnchorText = 'Play game!';
	
	commonApi.platformApi.postToFeed(obj, this);
}

function platformSendRequest(data) {
    var json = jQuery.parseJSON(data);

	var obj = {
		method : 'apprequests', 
		message : json.message,
		data :  json.data,
		group: json.group,
		crm_event_type: json.crm_event_type,
		type : json.type,
		product : json.product,
		product_detail : json.product_detail,
		ref_p_id : json.ref_p_id,
		ref_p_uid : json.ref_p_uid,
		ref_app_id : json.ref_app_id,
		ref_app_uid : json.ref_app_uid,
		platform_req_type_id : json.type_id,
	};
	if (json.to != null) {
		obj.to = json.to;
	} else {
		obj.filters = json.filters;
	}
	if (json.exclude_ids != null)
	{
		obj.exclude_ids = json.exclude_ids;
	}

    if (json.toPlatform != undefined && json.toPlatform != null) {
        obj.toPlatform = json.toPlatform;
    }

    if (json.title != undefined && json.title != null) {
        obj.title = json.title;
    }

    // G+
    obj.googleplusAnchorText = 'Play game!';
    obj.googleplusImages = ['https://web.archive.org/web/20140123030442/https://s3.amazonaws.com/tuxwars/googleplus/notification.png'];
    switch (obj.type) {
    case 0:
    case 1:
    case 5:
    case 6:
    	obj.googleplusType = 'gift';
    	break;
    case 7:
    case 10:
    	obj.googleplusType = 'invite';
    	break;
    default:
    	obj.googleplusType = 'message';
    	break;
    }

    if (json.forcedRequest != undefined) {
        obj.forcedRequest = json.forcedRequest;
    }

	commonApi.platformApi.sendRequest(obj, this);
}

function facebookBuyWithCredits(data) {
	var json = jQuery.parseJSON(data);
	var obj = {
		order_info : json.order_info,
		type : json.type,
        fullData : json
	};
	commonApi.platformApi.launchPremiumCurrency(obj, this);
}

// Start of offer EarnTuxWarsGold for all platform
function showEarnPage(data)
{
    var postdata = {
        "request_type":"purchase_currency_amount",
        "fb_id":this.platformUserId,
        "item_id":"",
        "platform":"2"
    };
    console.log("The data of the JSON From EarnTuxWarsGold" + JSON.stringify(postdata));
    jQuery.post(this.serverUrl + "FederalProxy",postdata,this.federalEarnGoldCallback,"json");
}
// End of of offer EarnTuxWarsGold for all platform

this.federalEarnGoldCallback = function(data) {
    var obj = data;
    console.log("federalEarnGoldCallback::The data of the JSON=" + JSON.stringify(data));
    FED.paymentWall(obj.federal,{
        "successCallback": this.successFedEarnArmyGoldCallback,
        "failureCallback": this.failureFedEarnArmyGoldCallback,
        "cancelCallback": this.cancelFedEarnArmyGoldCallback
    });
}
successFedEarnArmyGoldCallback = function(data) {
    console.log("successFedEarnArmyGoldCallback:: call back data ="+data);
    self.getGameFlashMovie().successCallback();
}
failureFedEarnArmyGoldCallback = function(data) {
    console.log("failureFedEarnArmyGoldCallback::data ="+data);
    self.getGameFlashMovie().cancelCallback();
}
cancelFedEarnArmyGoldCallback = function(data) {
    console.log("cancelFedEarnArmyGoldCallback::data ="+data);
    self.getGameFlashMovie().cancelCallback();
}
function placeOrder(data) {
	var json = jQuery.parseJSON(data);
	var obj = {
		order_info : json.order_info,
		type : json.type,
        fullData : json
	};
	commonApi.platformApi.launchPremiumCurrency(obj, this);
}

function showPaymentsUi(data){
	var json = jQuery.parseJSON(data);
	commonApi.platformApi.showPaymentsUi(json, this);
}

// Callbacks
	
function beforeFacebookCredits(data) {
	//crmTrackEvent("Economy", data.type, {"user_action" : "Started"});
}

function afterFacebookCredits(data, response) {
	if (response['order_id']) {
		var orderId = response['order_id']; 
		// CRM event sent in server
		toFlash("facebookCreditsBuyWithCreditsCallback", JSON.stringify({'success' : 1, 'orderId' : orderId}));
	} else {
		var errorCode = response['error_code'];
		var errorMessage = response['error_message'];
		//crmTrackEvent("Economy", data.type, {"user_action" : "Cancelled", "p1" : "errorCode: " + errorCode + "errorCode"});
		toFlash("facebookCreditsBuyWithCreditsCallback", JSON.stringify({'success' : 0, 'errorCode' : errorCode, 'errorMessage' : errorMessage}));
	}
}

function beforeFederalPayment(data) {
    //crmTrackEvent("Economy", data.type, {"user_action" : "Started"});
}

function afterFederalPayment(data, response) {
    if (response['payment_id']) {
        var orderId = response['payment_id'];
        // CRM event sent in server
        toFlash("afterFederalPayment", JSON.stringify({'success' : 1, 'orderId' : orderId, 'data' : data, 'type' : data.type}));
    } else {
        var errorCode = response['error_code'];
        var errorMessage = response['error_message'];
        //crmTrackEvent("Economy", data.type, {"user_action" : "Cancelled", "param_1" : "errorCode: " + errorCode + "errorCode"});
        toFlash("afterFederalPayment", JSON.stringify({'success' : 0, 'data' : data, 'type' : data.type, 'errorCode' : errorCode, 'errorMessage' : errorMessage}));
    }
}

function beforePostToFeedCallback(data) {
	var params = dataToParams(data);
	params["user_action"] = "Started";
	crmTrackEvent("Social", "Feed", params);
}

function afterPostToFeedCallback(data, response) {
	var params = dataToParams(data);
	if (response) {
		params["user_action"] = "Sent";
		crmTrackEvent("Social", "Feed", params);
		if (response.request){
			toFlash("facebookFeedPostedCallback", JSON.stringify({'success' : 1, 'request' : response.request, 'feedproperties' : data.feedproperties}));
		} else {
			toFlash("facebookFeedPostedCallback", JSON.stringify({'success' : 1, 'request' : null, 'feedproperties' : null}));
		}
	} else {
		params["user_action"] = "Cancelled";
		crmTrackEvent("Social", "Feed", params);
	}
}

function beforeSendRequestCallback(data) {
	toFlash("beforeSendRequestCallback", JSON.stringify({'type' : data.type, 'data' : data}));
}

function afterSendRequestCallback(data, response) {
	if (response && response.request) {
		toFlash("afterSendRequestCallback", JSON.stringify({'success' : 1, 'request' : response.request, 'to' : response.to, 'data' : data, 'type' : data.type, 'toPlatform' : response.toPlatform}));
	} else {
		toFlash("afterSendRequestCallback", JSON.stringify({'success' : 0, 'type' : data.type, 'data' : data}));
    }
}

// CRM
function crmReady(callback) {
	try{
		require(['crm-3'], function(Crm) {
			try{
				var crm = new Crm(crmKey, crmEnv, crmPid, platformUserId, crmAppId, dcgId, locale, {});
			} catch (ee){
				console.log('ERROR: '+ ee);
			}
			callback(crm);
		});
	} catch(e) {	}
}

function crmTrackEventByData(data) {
	var json = jQuery.parseJSON(data);
	
	var group = json.group;
	var type = json.type;
	var params = json.parameters;

	crmTrackEvent(group, type, params);
}

function crmTrackEvent(group, type, params) {
	if (eventsEnabled) {
		crmReady(function(crm) {
			if(crm != null){
				crm.track.event(group, type, params, {
						success: function(resp){
							console.log("crmTrackEvent success: " + resp);
						},
						error: function(resp) {
							console.log("crmTrackEvent error: " + resp);
						}					
				});
			}
		});
	}
}

function dataToParams(data) {
	//common params
	var params = {
			"group" : data.group,
			"ref_p_id" : data.ref_p_id,
			"ref_p_uid" : data.ref_p_uid,
			"ref_app_id" : data.ref_app_id,
			"ref_app_uid" : data.ref_app_uid
	};
	//event specific params
	if(data.crm_event_type) {
		params["type"] = data.crm_event_type;
	}
	if(data.product) {
		params["product"] = data.product;
	}
	if(data.value){
		params["value"] = data.value;
	}
	if(data.recipient_p_uids){
		params["recipient_p_uids"] = data.recipient_p_uids;
	}
	if(data.recipient_p_ids){
		params["recipient_p_ids"] = data.recipient_p_ids;
	}
	
	if (false) {
		if (!data.product) {
			alert("product missing: " + data);
		}
		if (!data.ref_p_id) {
			alert("ref_p_id missing: " + data);
		}
		if (!data.ref_p_uid) {
			alert("ref_p_uid missing: " + data);
		}
		if (!data.ref_app_id) {
			alert("ref_app_id missing: " + data);
		}
		if (!data.ref_app_uid) {
			alert("ref_app_uid missing: " + data);
		}
	}
	return params;
}

// Mousewheel
this.mouseWheel = function(event)
{
	
	var delta = 0;
	if (!event) // IE
		event = window.event;

	if (event.wheelDelta) // IE/Opera.
	{
		delta = event.wheelDelta/120;

		//Opera sign of delta is different than IE.
		if (window.opera)
			delta = -delta;
	}
	else if (event.detail)
	{
		// Mozilla sign of delta is different than IE.
		delta = -event.detail;
	}
	//Don't scroll the window
	if (event.preventDefault)
	{
		event.preventDefault();
	}

	event.returnValue = false;
	//forward to flash
	if (delta != 0) {
        toFlash("mouseWheelEvent", delta);
   	}
}

//add Mouse Wheel Listener
this.addMouseWheelListener = function()
{
	
	// Mouse wheel events to flash movie
	var movie = null;
    if (navigator.appName.indexOf("Microsoft") != -1) {
    	movie = window["flash"];
    } else {
    	movie = document["flash"];
    }
	if (movie)
	{
    		if(movie.attachEventListener) //For IE?
    		{
        		movie.attachEventListener("onmousewheel", this.mouseWheel);
		}
    		else if(movie.addEventListener) //for FF
    		{
        		movie.addEventListener('DOMMouseScroll', this.mouseWheel, false);
    		}
    		movie.onmousewheel = this.mouseWheel; //For Chrome/Opera
    	}
}


//This function loads the requireJS JavaScript API asyncronously after the 
//DOM of the game page has been fully loaded to the browser memory.
function loadWcrmRequireApi() {
	console.log("Creating script element for requireJS API [URL: " + wcrmRequireApiUrl + "]...");
 var scriptElement = document.createElement('script');
 scriptElement.type = 'text/javascript';
 scriptElement.async = true;
 scriptElement.onload = scriptElement.onreadystatechange = function (params) {
     if ((!this.readyState || this.readyState == "loaded" || this.readyState == "complete") && !requireJsApiLoaded) {
     	requireJsApiLoaded = true;
     	console.log("The requireJS API loaded successfully!", this);
     }
 };
 scriptElement.src = wcrmRequireApiUrl;
 var head = document.getElementsByTagName('head')[0];
 head.appendChild(scriptElement);
}

//This function loads the requireJS config asyncronously after the 
//requireJS JavaScript API has been fully loaded to the browser memor.
function loadWcrmRequireConfig() {
	if(requireJsApiLoaded) {
		console.log("Creating script element for requireJS config [URL: " + wcrmRequireConfigUrl + "]...");
		var scriptElement = document.createElement('script');
		scriptElement.type = 'text/javascript';
		scriptElement.async = true;
		scriptElement.onload = scriptElement.onreadystatechange = function (params) {
			if ((!this.readyState || this.readyState == "loaded" || this.readyState == "complete") && !requireJsConfigLoaded) {
				requireJsConfigLoaded = true;
				stopRequireJsConfigLoadingAndStartGame();
				clearTimeout(requireJsConfigLoadTimeOut);
				//since all the required JS dependencies for CRM tracking have been loaded, we can trigger the 
				// "Session Started OnIframe" CRM event here
				
		        var playerVersion = swfobject.getFlashPlayerVersion(); // returns a JavaScript object
		        var version = playerVersion.major + "." + playerVersion.minor + "." + playerVersion.release;
		        crmTrackEvent('Level', 'Session Started', {'user_action' : 'OnIframe', 'param_1' : version});
		        
				console.log("The requireJS config was loaded successfully!", this);
			}
		};
		scriptElement.src = wcrmRequireConfigUrl;
		var head = document.getElementsByTagName('head')[0];
		head.appendChild(scriptElement);		
	} 
}

//This function loads the requireJS config asyncronously after the 
//requireJS JavaScript API has been fully loaded to the browser memor.
function loadCBarJS() {
	console.log("Creating script element for CBar  [URL: " + wcrmCbarUrl + "]...");
	var scriptElement = document.createElement('script');
	scriptElement.type = 'text/javascript';
	scriptElement.async = true;
	scriptElement.onload = scriptElement.onreadystatechange = function (params) {
	if ((!this.readyState || this.readyState == "loaded" || this.readyState == "complete") && !CBarJsLoaded) {
				CBarJsLoaded = true;
				console.log("The CBarJS  was loaded successfully!", this);
		}
	};		
	scriptElement.src = wcrmCbarUrl;
	var head = document.getElementsByTagName('head')[0];
	head.appendChild(scriptElement);	
}

//This function is called if the browser is unable to load the 
//requireJS JavaScript API to the browser memory in 10000 ms.  
function stopRequireJsConfigLoadingAndStartGame() {
	if(!requireJsApiLoaded) {
		console.log("WARNING! Loading requireJS API failed or there was a timeout! CRM events will be disabled!");		
		eventsEnabled = false;
	}
	clearInterval(requireJsConfigLoadTimer);	
	loadCBarJS();
	canvasReady();
}

/*Added callback for TrialPay */
function afterTrialPayCredits(obj) {
    //credits indicate the no. of cash received from TrialPay
    toFlash("trialPayResponse", JSON.stringify({'success' : 1, 'completions' : obj.completions, 'credits' : obj.vc_amount}));
}

}
runFlash();

/*
     FILE ARCHIVED ON 03:04:42 Jan 23, 2014 AND RETRIEVED FROM THE
     INTERNET ARCHIVE ON 13:47:22 Jul 29, 2022.
     JAVASCRIPT APPENDED BY WAYBACK MACHINE, COPYRIGHT INTERNET ARCHIVE.

     ALL OTHER CONTENT MAY ALSO BE PROTECTED BY COPYRIGHT (17 U.S.C.
     SECTION 108(a)(3)).
*/
/*
playback timings (ms):
  captures_list: 327.898
  exclusion.robots: 131.793
  exclusion.robots.policy: 131.78
  xauthn.identify: 99.091
  xauthn.chkprivs: 32.369
  cdx.remote: 0.117
  esindex: 0.016
  LoadShardBlock: 156.982 (3)
  PetaboxLoader3.resolve: 126.937 (4)
  PetaboxLoader3.datanode: 112.51 (5)
  CDXLines.iter: 24.282 (3)
  load_resource: 131.859 (2)
*/