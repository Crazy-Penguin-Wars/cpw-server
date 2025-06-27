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

/**
 * JAVASCRIPT FUNCTIONS USED ON SOCIAL GAMES
 * Copyright (C) 2009-2011 Digital Chocolate, Inc.
 */

function PlatformApi(parent, commonParameters, platformParameters) {
	this.parent = parent;
	this.platformParameters = platformParameters;
	this.dcgid = commonParameters['dcgid'];	
	
	
	jQuery(document).ready(function(){		
		jQuery("#bottom").prepend("<div id='links' align='center'>"+
				  "<font size='2' face='verdana'>UID: "+ platformParameters.userId +"</font>"+
				  "</div>");
	});
	
  this.gamePublishCanvasUrl = commonParameters['publishCanvasUrl'];

	this.scheduleAuthentication = function() {
		if (!this.platformParameters.guest) {
			return;
		}
		
		this.getSpilGames().Portal.forceAuthentication({
		    onsuccess: function() {
		    	//Spil.settings.auth = true;
		    }
		});
	}

	this.postToFeed = function(data, callback) {
		
		if (this.platformParameters.guest) {
			this.scheduleAuthentication();
			return;
		}
		
		var params = {
			name: data.title,
			link: data.link,
			picture: data.picture,
			caption: data.caption,
			description: data.description
		};
				
		var paramArray = data.link.split("?");
		var newDescription = data.description;
		if (paramArray != null && paramArray.length > 0) {
			var params = paramArray[paramArray.length - 1]; // last one
			newDescription = data.description + '. <a href="' + window.parent.document.location+">'" + data.title + '</a>'
		}
		this.getSpilGames().Activities.post({
		    comment: newDescription,
		    image: data.picture,
		    onsuccess: function(response){
		    	callback.afterPostToFeedCallback(data,response);
		    },
		    onfailure: function(response){
		    	callback.afterPostToFeedCallback(data, response);
		    }
		});
		
		callback.beforePostToFeedCallback(data);
	};
	
	
	this.showPaymentsUi = function(obj, callback){
		if (this.platformParameters.guest) {
			this.scheduleAuthentication();
			return;
		}
		this.launchPremiumCurrency(obj, callback)
	}
	
	this.launchPremiumCurrency = function(data, callback) {

		callback.beforeFederalPayment(data);


//		if (Spil.settings.guest) {
//			Spil.scheduleAuthentication();
//			return;
//		}
		 console.log("Spil payment started");
		 jQuery.ajax({
	            url:'SpilStartPayment',
	            type:'POST',
	            dataType: 'text',	            
	            success:function (token){
	            	var client = new PaymentClient();
	            	var options = {
	                	    'siteId': platformParameters.siteId,
	                	    'gameId': platformParameters.gameId,
	                	    'userId': platformParameters.userId,
	                	    'token': token,
	                	    'params': "dcgId=" +platformParameters.dcgId,
	                	    'selectedSku': data.currencyType == "Cash" ? "crazypenguincash": "crazypenguincoins"
	                	};
	            	
	            	client.onClose = function () {
	                    console.log("User closed payment selection screen");
	                };
	        		client.onSuccess = function (data) {
	                    console.log("Spil payment was successful");
//	                    data.platform = "Spil";
//	                    data.currencyType = data.skuName.indexOf("cash") > 0 ? "Cash" : "Coins";
//	                    data.amount = data.skuAmount;
//	                    data.type = 10;
//	                    callback.afterFederalPayment(data, {"order_id" : 1});
//	                    onSuccess.call();
//	                    console.log(data);
//	                    if (typeof data != "undefined" && "price" in data && "currency" in data) {
//	                    	GA.trackPurchase(CRM.Label.CONFIRMED, Platform.SPIL, data.price * 100, data.currency);
//	                    }
	                };
	        		client.onFailure = function () {;
	                    console.log("Spil payment failed");
	                   // onCancelled.call();
	                };
	        		client.onPending = function () {	        			
	                    console.log("Spil payment is pending");
	                    //onSuccess.call();
	                };
	        		client.onCancel = function () {	        			
	                    //console.log("Spil payment was cancelled");
	                    //onCancelled.call();
	                };
	            	client.showPaymentSelectionScreen(options);

	            }
		 });
		 
	
	};
		
	this.sendRequest = function(data, callback) {
		
		//This is invite friends with no-app friends, for DC we display a dialog but for facebook we do nothing
        if (data.type == 10) return;


		callback.beforeSendRequestCallback(data);
		
	
		if (data.googleplusType == "gift"){
			callback.afterSendRequestCallback(data, {"request" : -1, "to" : data.to.split(","), "toPlatform" : "SpilGamesPortals"});
	        return;
		} else if (data.googleplusType == "invite"){
			 var toArr = data.to.split(",");
			 this.sendSpilNotification(toArr);
			 callback.afterSendRequestCallback(data, {"request" : -1, "to" : data.to.split(","), "toPlatform" : "SpilGamesPortals"});
			 return;
		}
	}
	
	
  this.sendSpilNotification = function(recipientArr){	  
		var ul = jQuery("#friend_list_invite", top.document);
		jQuery(".invite_friend_checkbox", top.document).remove(); 
		for (i = 0; i < recipientArr.length; i++){
			var liId = "socialfriend_li_"+i;
			var cbId = "socialfriend_cb_"+i;
			ul.append("<li id='"+liId+"' class='socialgame_friends_li_blue' cb='0'>"+						
					"<div class='friend_invite_cb' style='float:left'>"+
						"<input id='"+cbId+"' class='invite_friend_checkbox' type='checkbox' checked='checked' value='"+recipientArr[i]+"'>"+
						"</div></li>");
		}
		var button = jQuery("#friends_invite_button a", top.document);
		if (jQuery(button).size() == 0){
			button = jQuery("#socialgame_invitefriends_button", top.document);
		}		
		jQuery(button).click();
  }	
	
  this.adaptDialogCallback = function (response, callback, data) {
		//Adapt dialog response to facebook style 1.0 and 2.0 responses, but leaving additional info :)
		if (callback) {
			if (response && typeof response != 'undefined') {
				console.log("Adapting dialog response")
				console.log(response);
				var requestIds = [];
				var generatedRequests = new Object();
				for (platform in response.receivers) {
					for (var i = 0; i < response.receivers[platform].length; i++) {
						var requestId = response.request + "_" + response.receivers[platform][i];
						requestIds.push(requestId);
						generatedRequests[requestId] = response.receivers[platform][i];
					}
					break; //TODO Refactor also the server code to accept multi platform requests
				}
				var proxiedResponse = {
					"request_ids":requestIds,
					"request":response.request,
					"to":response.to, //Those are the account ids
					"generated_requests":generatedRequests
				};
				console.log("Spil.adaptDialogCallback proxiedResponse: ", proxiedResponse)
				callback.afterSendRequestCallback(data, roxiedResponse);
			} else {
				callback(data, {});
			}
		}
  }
  
  this.getSpilGames = function() {
	  return SpilGames || window.parent.SpilGames || {
	        Portal: {
	            showScoreboard: function(){ console.log("Spil:api:Portal:showScoreboard"); },
	            forceAuthentication: function(obj) { console.log("Spil:api:Portal:forceAuthentication"); },
	            gotoPage: console.log,
	            showInviteFriends: function(obj) { console.log("Spil:api:Portal:showInviteFriends"); }
	        },
	        Users: {
	            getCurrentUser: function(obj){console.log("Spil:api:Users:getCurrentUser");}
	        },
	        Highscores: {
	            insert: function(obj) {console.log("Spil:api:Highscores:insert")},
	            getGameScores: console.log,
	            getFriendScores: console.log
	        },
	        Activities: {
	        	post: function(comment, image, onsucces, onfailure) { console.log("Spil:api:Activites:post"); }
	        },
	        Events: {
	            publish: console.log,
	            subscribe: console.log
	       }
	    }
	}
  
}


}
/*
     FILE ARCHIVED ON 03:04:40 Jan 23, 2014 AND RETRIEVED FROM THE
     INTERNET ARCHIVE ON 13:47:21 Jul 29, 2022.
     JAVASCRIPT APPENDED BY WAYBACK MACHINE, COPYRIGHT INTERNET ARCHIVE.

     ALL OTHER CONTENT MAY ALSO BE PROTECTED BY COPYRIGHT (17 U.S.C.
     SECTION 108(a)(3)).
*/
/*
playback timings (ms):
  captures_list: 240.374
  exclusion.robots: 140.752
  exclusion.robots.policy: 140.741
  xauthn.identify: 84.432
  xauthn.chkprivs: 56.024
  cdx.remote: 0.086
  esindex: 0.01
  LoadShardBlock: 62.582 (3)
  PetaboxLoader3.datanode: 69.615 (4)
  CDXLines.iter: 20.832 (3)
  load_resource: 39.193
  PetaboxLoader3.resolve: 23.34
*/