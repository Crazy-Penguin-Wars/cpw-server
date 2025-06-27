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

/* cached on: Fri, 22 May 2020 21:05:12 GMT */ 
(function(h,d){var i=h.document,n=i.location,g=h.unescape,a=/sgapd=(https?:\/\/[a-z0-9.\-]+)/i.exec(g(n.search))||[0,""],o=function(){},m={},l=0,j=0,c=null,e={Cookies:["set"],Cache:["set"],Events:["publish","subscribe","subscribeOnce","unsubscribe"],Debug:["log","warn","error","subscribe","unsubscribe","publish","report"],Users:["get","getCurrentUser","getFriends"],Auth:["authenticate","login","logout"],Net:["post","get"],Highscores:["insert","getFriendScores","getMyScores","getGameScores"],Gameplay:["insert","getMyPlays","getFriendPlays"],Activities:["post","getActivityFeed"],Payments:["pay"],Portal:["getInformation","adjustHeight","requestGameBreak","showInviteFriends","showScoreboard","gotoPage","getLocale"]},f=function(){},k=function(s,r){if(h.postMessage){if(n!==h.parent.location){k=function(u,t){h.parent.postMessage(u,t)}}else{k=f}}else{k=f}k(s,r)},q=function(s){var t=JSON.parse(s.data),r=t.call.id.split(/^CALLBACK:/)[1]||0;if(m[t.id]&&m[t.id][r]){m[t.id][r](t.call.data)}},b=function(v,s,u){var t=s||0,r=u||function(){};if(!m[v]){m[v]={}}m[v][t]=r},p=function(r){return function(){var A=r+(+new Date()),z=[],u=arguments,v=null,y={id:A,call:[r]},w=0,t=0,s=0;for(w=0,s=u.length;w<s;w++){switch(typeof(u[w])){case"object":v={};for(t in u[w]){if(u[w].hasOwnProperty(t)){if(t.substr(0,2)==="on"){b(A,w+"."+t,u[w][t]);v[t]="CALLBACK:"+w+"."+t}else{v[t]=u[w][t]}}}z.push(v);break;case"function":b(A,w,u[w]);z.push("CALLBACK:"+w);break;default:z.push(arguments[w]);break}}y.call.push(z);k(JSON.stringify(y),a[1])}};for(l in e){if(e.hasOwnProperty(l)){o[l]={};for(j in e[l]){if(e[l].hasOwnProperty(j)){c="SpilGames."+l+"."+e[l][j];o[l][e[l][j]]=p(c)}}}}k("SpilGames.registerDomain",a[1]);if(h.attachEvent){h.attachEvent("onmessage",q,false)}else{if(h.addEventListener){h.addEventListener("message",q)}}h[(d||"SpilGames")]=o}(window));

}
/*
     FILE ARCHIVED ON 21:12:29 May 22, 2020 AND RETRIEVED FROM THE
     INTERNET ARCHIVE ON 13:47:36 Jul 29, 2022.
     JAVASCRIPT APPENDED BY WAYBACK MACHINE, COPYRIGHT INTERNET ARCHIVE.

     ALL OTHER CONTENT MAY ALSO BE PROTECTED BY COPYRIGHT (17 U.S.C.
     SECTION 108(a)(3)).
*/
/*
playback timings (ms):
  captures_list: 1915.019
  exclusion.robots: 106.103
  exclusion.robots.policy: 106.093
  xauthn.identify: 79.738
  xauthn.chkprivs: 26.067
  cdx.remote: 0.098
  esindex: 0.012
  LoadShardBlock: 105.999 (3)
  PetaboxLoader3.datanode: 233.662 (4)
  CDXLines.iter: 13.943 (3)
  load_resource: 294.602
  PetaboxLoader3.resolve: 119.201
*/