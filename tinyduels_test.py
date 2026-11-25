#!/usr/bin/env python3


# i have NO clue AT ALL what this does :skull:
# 100% claude, just a fun little test for Tiny Duels

# to connect the game: 1) find an ipa
#                      2) in the Payload/Penguin Wars.app folder, find the Info.plist file
#                      3) open it in a hex editor and replace the server url (if shorter, fill up with null characters 00)



"""
Minimal Crazy Penguin Wars / Tux Wars server.

Goal: get the client past startup (CHECK -> CREATE_ACCOUNT/LOGIN) onto the home screen.
Protocol (derived from the iOS binary, not from the original server):
  * HTTP POST, Content-Type application/x-protobuf (gzip request body tolerated)
  * body     = ituxwars.ServerRequestWrapper   { serverRequests[], signatures[] }
  * response = ituxwars.ServerResponseWrapper  { authenticated, serverResponses[], signatures[] }
  * signature (raw 16-byte MD5) = MD5( payload_bytes + gameSession + "PreCr4c4" )
    (the client verifies OUR signature and shows "Server signature error" if it is wrong)

Setup:  pip install flask protobuf
Run:    python server.py          (listens on 0.0.0.0:8080)
Then point "ServerUrl" in res/ituxwars_config.json at  <your-ip>:8080  (the game prepends "http://").
Every request is printed to the console and appended to server_log.txt.
"""
import base64, gzip, hashlib, json, os, time
from flask import Flask, request, Response
from google.protobuf import descriptor_pb2, descriptor_pool, text_format
try:
    from google.protobuf.message_factory import GetMessageClass
except ImportError:  # older protobuf
    from google.protobuf.message_factory import MessageFactory
    GetMessageClass = None

HOST, PORT = "0.0.0.0", 8000
SECRET = b"PreCr4c4"
FIRST_TIME_STATE = 0        # LoginResponse.firstTimeState; raise it if the client shows first-run hints
START_CASH, START_COINS = 1000, 100
DB_FILE = "users.json"
LOG_FILE = "server_log.txt"

START_ITEMS = {"BasicNuke": 100, "Pistol": 100}

_DESC_B64 = """
Cg5pdHV4d2Fycy5wcm90bxIIaXR1eHdhcnMiLgoNSW52ZW50b3J5SXRlbRIOCgZpdGVtSWQYASACKAkSDQoFY291bnQYAiACKAUi
NgoIU3luY0RhdGESDAoEY2FzaBgBIAIoBRINCgVjb2lucxgCIAIoBRINCgVzY29yZRgDIAIoBSK0AQoPQWNoaWV2ZW1lbnREYXRh
EkMKEHVzZXJBY2hpZXZlbWVudHMYASADKAsyKS5pdHV4d2Fycy5BY2hpZXZlbWVudERhdGEuVXNlckFjaGlldmVtZW50GlwKD1Vz
ZXJBY2hpZXZlbWVudBIVCg1hY2hpZXZlbWVudElkGAEgAigJEg0KBXZhbHVlGAIgAigFEhEKCWNvbXBsZXRlZBgDIAIoCBIQCghy
ZXdhcmRlZBgEIAIoCCJtCgpCYXR0bGVUdXJuEhIKCmJlZ2luU3RhdGUYAiACKAwSEAoIZW5kU3RhdGUYAyACKAwSEgoKcmVwbGF5
RGF0YRgEIAIoDBISCgp0dXJuV2VhcG9uGAUgASgJEhEKCXR1cm5TY29yZRgGIAEoBSLpKgoNU2VydmVyUmVxdWVzdBI2ChFzZXJ2
ZXJSZXF1ZXN0VHlwZRgBIAIoDjIbLml0dXh3YXJzLlNlcnZlclJlcXVlc3RUeXBlEg0KBWRjZ2lkGAIgASgDEg8KB2NvdW50ZXIY
AyABKAUSJAoIc3luY0RhdGEYBCABKAsyEi5pdHV4d2Fycy5TeW5jRGF0YRI8ChRzZXJ2ZXJSZXF1ZXN0Q2hhbm5lbBgFIAIoDjIe
Lml0dXh3YXJzLlNlcnZlclJlcXVlc3RDaGFubmVsEhcKD2NsaWVudFRpbWVTdGFtcBgGIAEoAxJACg9idXlDb2luc1JlcXVlc3QY
eSABKAsyJy5pdHV4d2Fycy5TZXJ2ZXJSZXF1ZXN0LkJ1eUNvaW5zUmVxdWVzdBI+Cg5idXlJdGVtUmVxdWVzdBhlIAEoCzImLml0
dXh3YXJzLlNlcnZlclJlcXVlc3QuQnV5SXRlbVJlcXVlc3QSRAoRY2hhbmdlTmlja1JlcXVlc3QYZiABKAsyKS5pdHV4d2Fycy5T
ZXJ2ZXJSZXF1ZXN0LkNoYW5nZU5pY2tSZXF1ZXN0EjoKDGNoZWNrUmVxdWVzdBhnIAEoCzIkLml0dXh3YXJzLlNlcnZlclJlcXVl
c3QuQ2hlY2tSZXF1ZXN0EkIKEGNoZWNrTmlja1JlcXVlc3QYaCABKAsyKC5pdHV4d2Fycy5TZXJ2ZXJSZXF1ZXN0LkNoZWNrTmlj
a1JlcXVlc3QSUAoXY29tcGxldGVUdXRvcmlhbFJlcXVlc3QYaSABKAsyLy5pdHV4d2Fycy5TZXJ2ZXJSZXF1ZXN0LkNvbXBsZXRl
VHV0b3JpYWxSZXF1ZXN0EkoKFGNyZWF0ZUFjY291bnRSZXF1ZXN0GGogASgLMiwuaXR1eHdhcnMuU2VydmVyUmVxdWVzdC5DcmVh
dGVBY2NvdW50UmVxdWVzdBJIChNjcmVhdGVCYXR0bGVSZXF1ZXN0GGsgASgLMisuaXR1eHdhcnMuU2VydmVyUmVxdWVzdC5DcmVh
dGVCYXR0bGVSZXF1ZXN0EkIKEGZpbmRNYXRjaFJlcXVlc3QYbCABKAsyKC5pdHV4d2Fycy5TZXJ2ZXJSZXF1ZXN0LkZpbmRNYXRj
aFJlcXVlc3QSYAofZ2FtZUNlbnRlclVzZXJJZHNUb0RnaWRzUmVxdWVzdBh1IAEoCzI3Lml0dXh3YXJzLlNlcnZlclJlcXVlc3Qu
R2FtZUNlbnRlclVzZXJJZHNUb0RnaWRzUmVxdWVzdBJCChBnZXRCYXR0bGVSZXF1ZXN0GG0gASgLMiguaXR1eHdhcnMuU2VydmVy
UmVxdWVzdC5HZXRCYXR0bGVSZXF1ZXN0Ej4KDmxldmVsVXBSZXF1ZXN0GHYgASgLMiYuaXR1eHdhcnMuU2VydmVyUmVxdWVzdC5M
ZXZlbFVwUmVxdWVzdBI6Cgxsb2dpblJlcXVlc3QYbiABKAsyJC5pdHV4d2Fycy5TZXJ2ZXJSZXF1ZXN0LkxvZ2luUmVxdWVzdBJE
ChFwYXltZW50SW9zUmVxdWVzdBh4IAEoCzIpLml0dXh3YXJzLlNlcnZlclJlcXVlc3QuUGF5bWVudElvc1JlcXVlc3QSTAoVcG9s
bEJhdHRsZUxpc3RSZXF1ZXN0GG8gASgLMi0uaXR1eHdhcnMuU2VydmVyUmVxdWVzdC5Qb2xsQmF0dGxlTGlzdFJlcXVlc3QSSAoT
c2VuZFJlbWluZGVyUmVxdWVzdBh0IAEoCzIrLml0dXh3YXJzLlNlcnZlclJlcXVlc3QuU2VuZFJlbWluZGVyUmVxdWVzdBJiCiBz
ZXRQdXNoTm90aWZpY2F0aW9uU3RhdHVzUmVxdWVzdBhwIAEoCzI4Lml0dXh3YXJzLlNlcnZlclJlcXVlc3QuU2V0UHVzaE5vdGlm
aWNhdGlvblN0YXR1c1JlcXVlc3QSUAoXc3VibWl0QmF0dGxlVHVyblJlcXVlc3QYcSABKAsyLy5pdHV4d2Fycy5TZXJ2ZXJSZXF1
ZXN0LlN1Ym1pdEJhdHRsZVR1cm5SZXF1ZXN0ElIKGHVwZGF0ZURldmljZVRva2VuUmVxdWVzdBhyIAEoCzIwLml0dXh3YXJzLlNl
cnZlclJlcXVlc3QuVXBkYXRlRGV2aWNlVG9rZW5SZXF1ZXN0ElgKG3VwZGF0ZUdhbWVDZW50ZXJJbmZvUmVxdWVzdBhzIAEoCzIz
Lml0dXh3YXJzLlNlcnZlclJlcXVlc3QuVXBkYXRlR2FtZUNlbnRlckluZm9SZXF1ZXN0ElQKGXVwZGF0ZVJhdGluZ1N0YXR1c1Jl
cXVlc3QYeiABKAsyMS5pdHV4d2Fycy5TZXJ2ZXJSZXF1ZXN0LlVwZGF0ZVJhdGluZ1N0YXR1c1JlcXVlc3QSSAoTZGVsZXRlQmF0
dGxlUmVxdWVzdBh7IAEoCzIrLml0dXh3YXJzLlNlcnZlclJlcXVlc3QuRGVsZXRlQmF0dGxlUmVxdWVzdBJOChZnZXRCYXR0bGVT
dGF0dXNSZXF1ZXN0GHwgASgLMi4uaXR1eHdhcnMuU2VydmVyUmVxdWVzdC5HZXRCYXR0bGVTdGF0dXNSZXF1ZXN0EkgKE3Jlc2Vy
dmVNYXRjaFJlcXVlc3QYfSABKAsyKy5pdHV4d2Fycy5TZXJ2ZXJSZXF1ZXN0LlJlc2VydmVNYXRjaFJlcXVlc3QSVAoZc2F2ZUZp
cnN0VGltZVN0YXRlUmVxdWVzdBh+IAEoCzIxLml0dXh3YXJzLlNlcnZlclJlcXVlc3QuU2F2ZUZpcnN0VGltZVN0YXRlUmVxdWVz
dBJKChRnZXRDdXN0b21pemVyUmVxdWVzdBh/IAEoCzIsLml0dXh3YXJzLlNlcnZlclJlcXVlc3QuR2V0Q3VzdG9taXplclJlcXVl
c3QSRwoScmVwb3J0RXJyb3JSZXF1ZXN0GIABIAEoCzIqLml0dXh3YXJzLlNlcnZlclJlcXVlc3QuUmVwb3J0RXJyb3JSZXF1ZXN0
ElsKHGNyZWF0ZUJhdHRsZVVzaW5nTmlja1JlcXVlc3QYgQEgASgLMjQuaXR1eHdhcnMuU2VydmVyUmVxdWVzdC5DcmVhdGVCYXR0
bGVVc2luZ05pY2tSZXF1ZXN0Ek8KFmFkZEluR2FtZUZyaWVuZFJlcXVlc3QYggEgASgLMi4uaXR1eHdhcnMuU2VydmVyUmVxdWVz
dC5BZGRJbkdhbWVGcmllbmRSZXF1ZXN0El8KHnJlcG9ydEFjaGlldmVtZW50U3RhdHVzUmVxdWVzdBiDASABKAsyNi5pdHV4d2Fy
cy5TZXJ2ZXJSZXF1ZXN0LlJlcG9ydEFjaGlldmVtZW50U3RhdHVzUmVxdWVzdBJhCh9jb2xsZWN0QWNoaWV2ZW1lbnRSZXdhcmRS
ZXF1ZXN0GIQBIAEoCzI3Lml0dXh3YXJzLlNlcnZlclJlcXVlc3QuQ29sbGVjdEFjaGlldmVtZW50UmV3YXJkUmVxdWVzdBJLChRn
ZXRDb25maWdEYXRhUmVxdWVzdBiFASABKAsyLC5pdHV4d2Fycy5TZXJ2ZXJSZXF1ZXN0LkdldENvbmZpZ0RhdGFSZXF1ZXN0ElkK
G2dldE5leHRPd25UdXJuQmF0dGxlUmVxdWVzdBiGASABKAsyMy5pdHV4d2Fycy5TZXJ2ZXJSZXF1ZXN0LkdldE5leHRPd25UdXJu
QmF0dGxlUmVxdWVzdBJVChlwYXltZW50SW9zRm9ySXRlbXNSZXF1ZXN0GIcBIAEoCzIxLml0dXh3YXJzLlNlcnZlclJlcXVlc3Qu
UGF5bWVudElvc0Zvckl0ZW1zUmVxdWVzdBpCCg5CdXlJdGVtUmVxdWVzdBIOCgZpdGVtSWQYASACKAkSEAoIaXNVbmxvY2sYAiAC
KAgSDgoGc291cmNlGAMgAigJGjYKD0J1eUNvaW5zUmVxdWVzdBITCgtnY1BhY2thZ2VJZBgBIAIoCRIOCgZzb3VyY2UYAiACKAka
IQoRQ2hhbmdlTmlja1JlcXVlc3QSDAoEbmljaxgBIAIoCRofCgxDaGVja1JlcXVlc3QSDwoHdmVyc2lvbhgBIAIoBRogChBDaGVj
a05pY2tSZXF1ZXN0EgwKBG5pY2sYASACKAkawgEKF0NvbXBsZXRlVHV0b3JpYWxSZXF1ZXN0EgwKBGNhc2gYASACKAMSDQoFY29p
bnMYAiACKAUSLwoOaW52ZW50b3J5SXRlbXMYDSADKAsyFy5pdHV4d2Fycy5JbnZlbnRvcnlJdGVtEhEKCWtpbGxDb3VudBgQIAIo
BRITCgtkYW1hZ2VQcm9wcxgRIAIoBRIfChdkYW1hZ2VIaXRQb2ludHNPcHBvbmVudBgSIAIoBRIQCghvd25TY29yZRgWIAIoBRoW
ChRDcmVhdGVBY2NvdW50UmVxdWVzdBpbChNDcmVhdGVCYXR0bGVSZXF1ZXN0EhUKDW9wcG9uZW50RGNnaWQYASACKAMSGgoSaXNH
YW1lQ2VudGVyRnJpZW5kGAIgAigIEhEKCWlzUmVtYXRjaBgDIAIoCBomChBGaW5kTWF0Y2hSZXF1ZXN0EhIKCmZvcmNlU3RhcnQY
ASACKAgaPAofR2FtZUNlbnRlclVzZXJJZHNUb0RnaWRzUmVxdWVzdBIZChFnYW1lQ2VudGVyVXNlcklkcxgBIAMoCRpXChBHZXRC
YXR0bGVSZXF1ZXN0EhAKCGJhdHRsZUlkGAEgAigDEhgKEGJhdHRsZU93bmVyRGNnaWQYAiACKAMSFwoPaW5jbHVkZVR1cm5EYXRh
GAMgAigIGhAKDkxldmVsVXBSZXF1ZXN0Gn4KDExvZ2luUmVxdWVzdBITCgtmYWNlYm9va1VpZBgBIAEoCRIbChNmYWNlYm9va0Fj
Y2Vzc1Rva2VuGAIgASgJEhAKCHRpbWV6b25lGAMgASgFEg8KB3ZlcnNpb24YBCACKAUSGQoRaU1CUGxhdGZvcm1Vc2VySWQYBSAC
KAkaaAoRUGF5bWVudElvc1JlcXVlc3QSEwoLcmVjZWlwdERhdGEYASACKAwSEQoJcGFja2FnZUlkGAIgAigJEhQKDGN1cnJlbmN5
Q29kZRgDIAIoCRIVCg10cmFuc2FjdGlvbklkGAQgAigJGhcKFVBvbGxCYXR0bGVMaXN0UmVxdWVzdBpZChNTZW5kUmVtaW5kZXJS
ZXF1ZXN0EhYKDnJlY2lwaWVudERjZ2lkGAEgAigDEhAKCGJhdHRsZUlkGAIgAigDEhgKEGJhdHRsZU93bmVyRGNnaWQYAyACKAMa
VwogU2V0UHVzaE5vdGlmaWNhdGlvblN0YXR1c1JlcXVlc3QSIgoacHVzaE5vdGlmaWNhdGlvbkNhdGVnb3J5SWQYASACKAUSDwoH
ZW5hYmxlZBgCIAIoCBqEAgoXU3VibWl0QmF0dGxlVHVyblJlcXVlc3QSEAoIYmF0dGxlSWQYASACKAMSGAoQYmF0dGxlT3duZXJE
Y2dpZBgCIAIoAxITCgtmaW5pc2hlZEFjaxgEIAIoCBIMCgRxdWl0GAUgAigIEigKCmJhdHRsZVR1cm4YByACKAsyFC5pdHV4d2Fy
cy5CYXR0bGVUdXJuEhEKCWtpbGxDb3VudBgQIAIoBRITCgtkYW1hZ2VQcm9wcxgRIAIoBRIfChdkYW1hZ2VIaXRQb2ludHNPcHBv
bmVudBgSIAIoBRIQCghvd25TY29yZRgWIAIoBRIVCg1vcHBvbmVudFNjb3JlGBcgAigFGlsKGFVwZGF0ZURldmljZVRva2VuUmVx
dWVzdBISCgpwbGF0Zm9ybUlkGAEgAigFEhYKDm9sZERldmljZVRva2VuGAIgASgJEhMKC2RldmljZVRva2VuGAMgAigJGk8KG1Vw
ZGF0ZUdhbWVDZW50ZXJJbmZvUmVxdWVzdBIYChBnYW1lQ2VudGVyVXNlcklkGAEgAigJEhYKDmdhbWVDZW50ZXJOYW1lGAIgAigJ
GkwKGVVwZGF0ZVJhdGluZ1N0YXR1c1JlcXVlc3QSLwoMcmF0aW5nU3RhdHVzGAEgAigOMhkuaXR1eHdhcnMuQXBwUmF0aW5nU3Rh
dHVzGkEKE0RlbGV0ZUJhdHRsZVJlcXVlc3QSEAoIYmF0dGxlSWQYASACKAMSGAoQYmF0dGxlT3duZXJEY2dpZBgCIAIoAxpEChZH
ZXRCYXR0bGVTdGF0dXNSZXF1ZXN0EhAKCGJhdHRsZUlkGAEgAigDEhgKEGJhdHRsZU93bmVyRGNnaWQYAiACKAMaJgoTUmVzZXJ2
ZU1hdGNoUmVxdWVzdBIPCgdyZXNlcnZlGAEgAigIGioKGVNhdmVGaXJzdFRpbWVTdGF0ZVJlcXVlc3QSDQoFc3RhdGUYASACKAUa
FgoUR2V0Q3VzdG9taXplclJlcXVlc3QaNwoSUmVwb3J0RXJyb3JSZXF1ZXN0Eg0KBXBsYWNlGAEgASgJEhIKCnN0YWNrVHJhY2UY
AiACKAkaNAocQ3JlYXRlQmF0dGxlVXNpbmdOaWNrUmVxdWVzdBIUCgxvcHBvbmVudE5pY2sYASACKAkaLQoWQWRkSW5HYW1lRnJp
ZW5kUmVxdWVzdBITCgtmcmllbmREY2dJZBgBIAIoAxquAQoeUmVwb3J0QWNoaWV2ZW1lbnRTdGF0dXNSZXF1ZXN0El4KD3VwZGF0
ZWRDb3VudGVycxgBIAMoCzJFLml0dXh3YXJzLlNlcnZlclJlcXVlc3QuUmVwb3J0QWNoaWV2ZW1lbnRTdGF0dXNSZXF1ZXN0LlVw
ZGF0ZWRDb3VudGVyGiwKDlVwZGF0ZWRDb3VudGVyEgsKA2tleRgBIAIoCRINCgV2YWx1ZRgCIAIoBRo4Ch9Db2xsZWN0QWNoaWV2
ZW1lbnRSZXdhcmRSZXF1ZXN0EhUKDWFjaGlldmVtZW50SWQYASACKAkaFgoUR2V0Q29uZmlnRGF0YVJlcXVlc3QaZQobR2V0TmV4
dE93blR1cm5CYXR0bGVSZXF1ZXN0EhcKD2luY2x1ZGVUdXJuRGF0YRgBIAIoCBIVCg1leGNlcHRPd25lcklkGAIgAigDEhYKDmV4
Y2VwdEJhdHRsZUlkGAMgAigDGnEKGVBheW1lbnRJb3NGb3JJdGVtc1JlcXVlc3QSEwoLcmVjZWlwdERhdGEYASACKAwSFAoMY3Vy
cmVuY3lDb2RlGAMgAigJEhUKDXRyYW5zYWN0aW9uSWQYBCACKAkSEgoKaXNSZXN0b3JlZBgFIAIoCCJCChRTZXJ2ZXJSZXF1ZXN0
V3JhcHBlchIWCg5zZXJ2ZXJSZXF1ZXN0cxgBIAMoDBISCgpzaWduYXR1cmVzGAIgAygMIuBCCg5TZXJ2ZXJSZXNwb25zZRI2ChFz
ZXJ2ZXJSZXF1ZXN0VHlwZRgBIAIoDjIbLml0dXh3YXJzLlNlcnZlclJlcXVlc3RUeXBlEkUKDHJlc3BvbnNlQ29kZRgCIAEoDjIr
Lml0dXh3YXJzLlNlcnZlclJlc3BvbnNlLlNlcnZlclJlc3BvbnNlQ29kZToCT0sSFwoPcmVzcG9uc2VNZXNzYWdlGAMgASgJEg8K
B2NvdW50ZXIYBCABKAUSJAoIc3luY0RhdGEYBSABKAsyEi5pdHV4d2Fycy5TeW5jRGF0YRI8ChRzZXJ2ZXJSZXF1ZXN0Q2hhbm5l
bBgGIAIoDjIeLml0dXh3YXJzLlNlcnZlclJlcXVlc3RDaGFubmVsEjIKD2FjaGlldmVtZW50RGF0YRgHIAEoCzIZLml0dXh3YXJz
LkFjaGlldmVtZW50RGF0YRJDChBidXlDb2luc1Jlc3BvbnNlGHkgASgLMikuaXR1eHdhcnMuU2VydmVyUmVzcG9uc2UuQnV5Q29p
bnNSZXNwb25zZRJBCg9idXlJdGVtUmVzcG9uc2UYZSABKAsyKC5pdHV4d2Fycy5TZXJ2ZXJSZXNwb25zZS5CdXlJdGVtUmVzcG9u
c2USRwoSY2hhbmdlTmlja1Jlc3BvbnNlGGYgASgLMisuaXR1eHdhcnMuU2VydmVyUmVzcG9uc2UuQ2hhbmdlTmlja1Jlc3BvbnNl
Ej0KDWNoZWNrUmVzcG9uc2UYZyABKAsyJi5pdHV4d2Fycy5TZXJ2ZXJSZXNwb25zZS5DaGVja1Jlc3BvbnNlEkUKEWNoZWNrTmlj
a1Jlc3BvbnNlGGggASgLMiouaXR1eHdhcnMuU2VydmVyUmVzcG9uc2UuQ2hlY2tOaWNrUmVzcG9uc2USUwoYY29tcGxldGVUdXRv
cmlhbFJlc3BvbnNlGGkgASgLMjEuaXR1eHdhcnMuU2VydmVyUmVzcG9uc2UuQ29tcGxldGVUdXRvcmlhbFJlc3BvbnNlEk0KFWNy
ZWF0ZUFjY291bnRSZXNwb25zZRhqIAEoCzIuLml0dXh3YXJzLlNlcnZlclJlc3BvbnNlLkNyZWF0ZUFjY291bnRSZXNwb25zZRJL
ChRjcmVhdGVCYXR0bGVSZXNwb25zZRhrIAEoCzItLml0dXh3YXJzLlNlcnZlclJlc3BvbnNlLkNyZWF0ZUJhdHRsZVJlc3BvbnNl
EkUKEWZpbmRNYXRjaFJlc3BvbnNlGGwgASgLMiouaXR1eHdhcnMuU2VydmVyUmVzcG9uc2UuRmluZE1hdGNoUmVzcG9uc2USYwog
Z2FtZUNlbnRlclVzZXJJZHNUb0RnaWRzUmVzcG9uc2UYdSABKAsyOS5pdHV4d2Fycy5TZXJ2ZXJSZXNwb25zZS5HYW1lQ2VudGVy
VXNlcklkc1RvRGdpZHNSZXNwb25zZRJFChFnZXRCYXR0bGVSZXNwb25zZRhtIAEoCzIqLml0dXh3YXJzLlNlcnZlclJlc3BvbnNl
LkdldEJhdHRsZVJlc3BvbnNlEkEKD2xldmVsVXBSZXNwb25zZRh2IAEoCzIoLml0dXh3YXJzLlNlcnZlclJlc3BvbnNlLkxldmVs
VXBSZXNwb25zZRI9Cg1sb2dpblJlc3BvbnNlGG4gASgLMiYuaXR1eHdhcnMuU2VydmVyUmVzcG9uc2UuTG9naW5SZXNwb25zZRJH
ChJwYXltZW50SW9zUmVzcG9uc2UYeCABKAsyKy5pdHV4d2Fycy5TZXJ2ZXJSZXNwb25zZS5QYXltZW50SW9zUmVzcG9uc2USTwoW
cG9sbEJhdHRsZUxpc3RSZXNwb25zZRhvIAEoCzIvLml0dXh3YXJzLlNlcnZlclJlc3BvbnNlLlBvbGxCYXR0bGVMaXN0UmVzcG9u
c2USSwoUc2VuZFJlbWluZGVyUmVzcG9uc2UYdCABKAsyLS5pdHV4d2Fycy5TZXJ2ZXJSZXNwb25zZS5TZW5kUmVtaW5kZXJSZXNw
b25zZRJlCiFzZXRQdXNoTm90aWZpY2F0aW9uU3RhdHVzUmVzcG9uc2UYcCABKAsyOi5pdHV4d2Fycy5TZXJ2ZXJSZXNwb25zZS5T
ZXRQdXNoTm90aWZpY2F0aW9uU3RhdHVzUmVzcG9uc2USUwoYc3VibWl0QmF0dGxlVHVyblJlc3BvbnNlGHEgASgLMjEuaXR1eHdh
cnMuU2VydmVyUmVzcG9uc2UuU3VibWl0QmF0dGxlVHVyblJlc3BvbnNlElUKGXVwZGF0ZURldmljZVRva2VuUmVzcG9uc2UYciAB
KAsyMi5pdHV4d2Fycy5TZXJ2ZXJSZXNwb25zZS5VcGRhdGVEZXZpY2VUb2tlblJlc3BvbnNlElsKHHVwZGF0ZUdhbWVDZW50ZXJJ
bmZvUmVzcG9uc2UYcyABKAsyNS5pdHV4d2Fycy5TZXJ2ZXJSZXNwb25zZS5VcGRhdGVHYW1lQ2VudGVySW5mb1Jlc3BvbnNlElcK
GnVwZGF0ZVJhdGluZ1N0YXR1c1Jlc3BvbnNlGHogASgLMjMuaXR1eHdhcnMuU2VydmVyUmVzcG9uc2UuVXBkYXRlUmF0aW5nU3Rh
dHVzUmVzcG9uc2USSwoUZGVsZXRlQmF0dGxlUmVzcG9uc2UYeyABKAsyLS5pdHV4d2Fycy5TZXJ2ZXJSZXNwb25zZS5EZWxldGVC
YXR0bGVSZXNwb25zZRJRChdnZXRCYXR0bGVTdGF0dXNSZXNwb25zZRh8IAEoCzIwLml0dXh3YXJzLlNlcnZlclJlc3BvbnNlLkdl
dEJhdHRsZVN0YXR1c1Jlc3BvbnNlEksKFHJlc2VydmVNYXRjaFJlc3BvbnNlGH0gASgLMi0uaXR1eHdhcnMuU2VydmVyUmVzcG9u
c2UuUmVzZXJ2ZU1hdGNoUmVzcG9uc2USVwoac2F2ZUZpcnN0VGltZVN0YXRlUmVzcG9uc2UYfiABKAsyMy5pdHV4d2Fycy5TZXJ2
ZXJSZXNwb25zZS5TYXZlRmlyc3RUaW1lU3RhdGVSZXNwb25zZRJNChVnZXRDdXN0b21pemVyUmVzcG9uc2UYfyABKAsyLi5pdHV4
d2Fycy5TZXJ2ZXJSZXNwb25zZS5HZXRDdXN0b21pemVyUmVzcG9uc2USSgoTcmVwb3J0RXJyb3JSZXNwb25zZRiAASABKAsyLC5p
dHV4d2Fycy5TZXJ2ZXJSZXNwb25zZS5SZXBvcnRFcnJvclJlc3BvbnNlEl4KHWNyZWF0ZUJhdHRsZVVzaW5nTmlja1Jlc3BvbnNl
GIEBIAEoCzI2Lml0dXh3YXJzLlNlcnZlclJlc3BvbnNlLkNyZWF0ZUJhdHRsZVVzaW5nTmlja1Jlc3BvbnNlElIKF2FkZEluR2Ft
ZUZyaWVuZFJlc3BvbnNlGIIBIAEoCzIwLml0dXh3YXJzLlNlcnZlclJlc3BvbnNlLkFkZEluR2FtZUZyaWVuZFJlc3BvbnNlEmIK
H3JlcG9ydEFjaGlldmVtZW50U3RhdHVzUmVzcG9uc2UYgwEgASgLMjguaXR1eHdhcnMuU2VydmVyUmVzcG9uc2UuUmVwb3J0QWNo
aWV2ZW1lbnRTdGF0dXNSZXNwb25zZRJkCiBjb2xsZWN0QWNoaWV2ZW1lbnRSZXdhcmRSZXNwb25zZRiEASABKAsyOS5pdHV4d2Fy
cy5TZXJ2ZXJSZXNwb25zZS5Db2xsZWN0QWNoaWV2ZW1lbnRSZXdhcmRSZXNwb25zZRJOChVnZXRDb25maWdEYXRhUmVzcG9uc2UY
hQEgASgLMi4uaXR1eHdhcnMuU2VydmVyUmVzcG9uc2UuR2V0Q29uZmlnRGF0YVJlc3BvbnNlElwKHGdldE5leHRPd25UdXJuQmF0
dGxlUmVzcG9uc2UYhgEgASgLMjUuaXR1eHdhcnMuU2VydmVyUmVzcG9uc2UuR2V0TmV4dE93blR1cm5CYXR0bGVSZXNwb25zZRJY
ChpwYXltZW50SW9zRm9ySXRlbXNSZXNwb25zZRiHASABKAsyMy5pdHV4d2Fycy5TZXJ2ZXJSZXNwb25zZS5QYXltZW50SW9zRm9y
SXRlbXNSZXNwb25zZRrMBAoGQmF0dGxlEgoKAmlkGAEgAigDEhMKC2xhc3RUdXJuQWdlGAIgASgFEhIKCnR1cm5zQ291bnQYAyAC
KAUSJgoIbGFzdFR1cm4YBCABKAsyFC5pdHV4d2Fycy5CYXR0bGVUdXJuEg0KBWxldmVsGAUgAigJEiQKBXN0YXRlGAYgAigOMhUu
aXR1eHdhcnMuQmF0dGxlU3RhdGUSEwoLd2lubmVyRGNnaWQYByABKAMSHAoUaXNPcHBvbmVudGxlc3NCYXR0bGUYCCACKAgSEgoK
b3duZXJEY2dpZBgLIAIoAxIVCg1jYW5OdWRnZUFmdGVyGAwgASgFEhUKDW9wcG9uZW50RGNnaWQYFSACKAMSFAoMb3Bwb25lbnRO
YW1lGBYgAigJEhcKD29wcG9uZW50UGljdHVyZRgXIAIoCRIeChZvcHBvbmVudEZhY2Vib29rVXNlcklkGBggASgJEiAKGG9wcG9u
ZW50R2FtZUNlbnRlclVzZXJJZBgZIAEoCRIZChFvcHBvbmVudEtpbGxDb3VudBgaIAIoBRIbChNvcHBvbmVudERhbWFnZVByb3Bz
GBsgAigFEh8KF29wcG9uZW50RGFtYWdlSGl0UG9pbnRzGBwgAigFEhUKDW9wcG9uZW50U2NvcmUYHSACKAUSFAoMb3duS2lsbENv
dW50GCQgAigFEhYKDm93bkRhbWFnZVByb3BzGCUgAigFEhoKEm93bkRhbWFnZUhpdFBvaW50cxgmIAIoBRIQCghvd25TY29yZRgn
IAIoBRq2AQoHQmF0dGxlcxI4Cg95b3VyVHVybkJhdHRsZXMYAiADKAsyHy5pdHV4d2Fycy5TZXJ2ZXJSZXNwb25zZS5CYXR0bGUS
NwoOd2FpdGluZ0JhdHRsZXMYAyADKAsyHy5pdHV4d2Fycy5TZXJ2ZXJSZXNwb25zZS5CYXR0bGUSOAoPZmluaXNoZWRCYXR0bGVz
GAQgAygLMh8uaXR1eHdhcnMuU2VydmVyUmVzcG9uc2UuQmF0dGxlGhIKEEJ1eUNvaW5zUmVzcG9uc2UaEQoPQnV5SXRlbVJlc3Bv
bnNlGjgKEkNoYW5nZU5pY2tSZXNwb25zZRIKCgJvaxgBIAIoCBIWCg5zdWdnZXN0ZWROaWNrcxgCIAMoCRqXAQoNQ2hlY2tSZXNw
b25zZRIVCg1zZXJ2ZXJWZXJzaW9uGAEgAigFEhwKFHNlcnZlck1pbmltdW1WZXJzaW9uGAIgAigFEh0KFWludmFsaWRWZXJzaW9u
TWVzc2FnZRgDIAIoCRIbChNob3RDaG9jb2xhdGVNZXNzYWdlGAQgAigJEhUKDW5ld1ZlcnNpb25VcmwYBSABKAkaNwoRQ2hlY2tO
aWNrUmVzcG9uc2USCgoCb2sYASACKAgSFgoOc3VnZ2VzdGVkTmlja3MYAiADKAkagwEKGENvbXBsZXRlVHV0b3JpYWxSZXNwb25z
ZRIUCgxyZXdhcmRYcEdhbWUYASACKAUSFwoPcmV3YXJkQ29pbnNHYW1lGAUgAigFEhgKEHJld2FyZENvaW5zQm9udXMYBiACKAUS
HgoWcmV3YXJkQ29pbnNEZXN0cnVjdGlvbhgHIAIoBRpJChVDcmVhdGVBY2NvdW50UmVzcG9uc2USDQoFZGNnaWQYASACKAMSEwoL
Z2FtZVNlc3Npb24YAiACKAkSDAoEbmljaxgDIAIoCRpHChRDcmVhdGVCYXR0bGVSZXNwb25zZRIvCgZiYXR0bGUYASACKAsyHy5p
dHV4d2Fycy5TZXJ2ZXJSZXNwb25zZS5CYXR0bGUa0AEKEUZpbmRNYXRjaFJlc3BvbnNlElcKEW1hdGNoUmVzcG9uc2VUeXBlGAEg
AigOMjwuaXR1eHdhcnMuU2VydmVyUmVzcG9uc2UuRmluZE1hdGNoUmVzcG9uc2UuTWF0Y2hSZXNwb25zZVR5cGUSLwoGYmF0dGxl
GAIgASgLMh8uaXR1eHdhcnMuU2VydmVyUmVzcG9uc2UuQmF0dGxlIjEKEU1hdGNoUmVzcG9uc2VUeXBlEgsKB1dBSVRJTkcQABIP
CgtNQVRDSF9GT1VORBABGssBCiBHYW1lQ2VudGVyVXNlcklkc1RvRGdpZHNSZXNwb25zZRJoChJnYW1lQ2VudGVyVXNlckluZm8Y
ASADKAsyTC5pdHV4d2Fycy5TZXJ2ZXJSZXNwb25zZS5HYW1lQ2VudGVyVXNlcklkc1RvRGdpZHNSZXNwb25zZS5HYW1lQ2VudGVy
VXNlckluZm8aPQoSR2FtZUNlbnRlclVzZXJJbmZvEhgKEGdhbWVDZW50ZXJVc2VySWQYASACKAkSDQoFZGNnaWQYAiACKAMaRAoR
R2V0QmF0dGxlUmVzcG9uc2USLwoGYmF0dGxlGAEgAigLMh8uaXR1eHdhcnMuU2VydmVyUmVzcG9uc2UuQmF0dGxlGhEKD0xldmVs
VXBSZXNwb25zZRrmCwoNTG9naW5SZXNwb25zZRINCgVkY2dpZBgBIAIoAxITCgtnYW1lU2Vzc2lvbhgCIAIoCRIMCgRuaWNrGAMg
AigJEgwKBGNhc2gYBCACKAMSDQoFY29pbnMYBSACKAUSDQoFc2NvcmUYBiACKAMSGQoRdHV0b3JpYWxDb21wbGV0ZWQYByACKAgS
EwoLZmFjZWJvb2tVaWQYCCABKAkSFAoMZmFjZWJvb2tOYW1lGBAgASgJEhoKEmZhY2Vib29rUGljdHVyZVVybBgTIAEoCRIVCg1n
YW1lQ2VudGVyVWlkGAkgASgJEhUKDWNhbkNoYW5nZU5pY2sYCyACKAgSVwoUZmFjZWJvb2tGcmllbmRzRGF0YXMYDCADKAsyOS5p
dHV4d2Fycy5TZXJ2ZXJSZXNwb25zZS5Mb2dpblJlc3BvbnNlLkZhY2Vib29rRnJpZW5kRGF0YRIvCg5pbnZlbnRvcnlJdGVtcxgN
IAMoCzIXLml0dXh3YXJzLkludmVudG9yeUl0ZW0SKwojZGlzYWJsZWRQdXNoTm90aWZpY2F0aW9uQ2F0ZWdvcnlJZHMYDiADKAUS
SgoNcGNQcmljZXBvaW50cxgPIAMoCzIzLml0dXh3YXJzLlNlcnZlclJlc3BvbnNlLkxvZ2luUmVzcG9uc2UuUENQcmljZXBvaW50
EkoKDWdjUHJpY2Vwb2ludHMYEiADKAsyMy5pdHV4d2Fycy5TZXJ2ZXJSZXNwb25zZS5Mb2dpblJlc3BvbnNlLkdDUHJpY2Vwb2lu
dBITCgtzeW5jRW5hYmxlZBgRIAIoCBIYChBzaG93UmF0aW5nU2NyZWVuGBQgASgIEhYKDmZpcnN0VGltZVN0YXRlGBUgAigFEi4K
DWN1c3RvbUNvbnRlbnQYFiABKAsyFy5pdHV4d2Fycy5DdXN0b21Db250ZW50EkwKDnNhdmVkVXNlckRhdGFzGBcgAygLMjQuaXR1
eHdhcnMuU2VydmVyUmVzcG9uc2UuTG9naW5SZXNwb25zZS5TYXZlZFVzZXJEYXRhEiwKDHBvcHVwQ29udGVudBgYIAEoCzIWLml0
dXh3YXJzLlBvcHVwQ29udGVudBIyCg9hY2hpZXZlbWVudERhdGEYGSACKAsyGS5pdHV4d2Fycy5BY2hpZXZlbWVudERhdGEacQoS
RmFjZWJvb2tGcmllbmREYXRhEg0KBWRjZ2lkGAEgAigDEhMKC2ZhY2Vib29rVWlkGAIgAigJEhEKCWZpcnN0TmFtZRgDIAIoCRIQ
CghsYXN0TmFtZRgEIAIoCRISCgpwaWN0dXJlVXJsGAUgAigJGiwKDVNhdmVkVXNlckRhdGESDQoFZGNnaWQYASACKAMSDAoEbmlj
axgCIAIoCRr6AQoMUENQcmljZXBvaW50EgoKAmlkGAEgAigJEhAKCHZlbmRvcklkGAIgAigJEg4KBmFtb3VudBgDIAIoBRITCgtl
eHRyYUFtb3VudBgEIAIoBRITCgt1c2RDZW50Q29zdBgFIAIoBRIUCgxzb3J0UHJpb3JpdHkYBiACKAUSDAoEbmFtZRgHIAIoCRIT
CgtkZXNjcmlwdGlvbhgIIAIoCRITCgtleHBvcnRJbWFnZRgJIAIoCRIPCgdlbmFibGVkGAogAigIEhYKDm9yaWdpbmFsQW1vdW50
GAsgASgFEhsKE29yaWdpbmFsRXh0cmFBbW91bnQYDCABKAUa0gEKDEdDUHJpY2Vwb2ludBIKCgJpZBgBIAIoCRIOCgZhbW91bnQY
AiACKAUSEwoLZXh0cmFBbW91bnQYAyACKAUSDgoGcGNDb3N0GAQgAigFEhQKDHNvcnRQcmlvcml0eRgGIAIoBRIMCgRuYW1lGAcg
AigJEhMKC2Rlc2NyaXB0aW9uGAggAigJEhMKC2V4cG9ydEltYWdlGAkgAigJEhYKDm9yaWdpbmFsQW1vdW50GAogASgFEhsKE29y
aWdpbmFsRXh0cmFBbW91bnQYCyABKAUaYwoSUGF5bWVudElvc1Jlc3BvbnNlEg8KB3N1Y2Nlc3MYASACKAgSEQoJY2FzaEFkZGVk
GAIgAigFEhUKDXRyYW5zYWN0aW9uSWQYAyABKAkSEgoKY29pbnNBZGRlZBgEIAIoBRpLChZQb2xsQmF0dGxlTGlzdFJlc3BvbnNl
EjEKB2JhdHRsZXMYASACKAsyIC5pdHV4d2Fycy5TZXJ2ZXJSZXNwb25zZS5CYXR0bGVzGhYKFFNlbmRSZW1pbmRlclJlc3BvbnNl
GiMKIVNldFB1c2hOb3RpZmljYXRpb25TdGF0dXNSZXNwb25zZRqwAgoYU3VibWl0QmF0dGxlVHVyblJlc3BvbnNlEhQKDHJld2Fy
ZFhwR2FtZRgBIAEoBRIXCg9yZXdhcmRDb2luc0dhbWUYBSABKAUSGAoQcmV3YXJkQ29pbnNCb251cxgGIAEoBRIeChZyZXdhcmRD
b2luc0Rlc3RydWN0aW9uGAcgASgFEhAKCHdpbkNvdW50GAggASgFEhEKCWtpbGxDb3VudBgJIAEoBRITCgt3aW5uZXJEY2dpZBgK
IAEoAxIYChBzaG93UmF0aW5nU2NyZWVuGAsgASgIEiQKBXN0YXRlGAwgAigOMhUuaXR1eHdhcnMuQmF0dGxlU3RhdGUSFwoPd29u
QWdhaW5zdENvdW50GA0gASgFEhgKEGxvc3RBZ2FpbnN0Q291bnQYDiABKAUaGwoZVXBkYXRlRGV2aWNlVG9rZW5SZXNwb25zZRoe
ChxVcGRhdGVHYW1lQ2VudGVySW5mb1Jlc3BvbnNlGhwKGlVwZGF0ZVJhdGluZ1N0YXR1c1Jlc3BvbnNlGhYKFERlbGV0ZUJhdHRs
ZVJlc3BvbnNlGu4BChdHZXRCYXR0bGVTdGF0dXNSZXNwb25zZRIQCghiYXR0bGVJZBgBIAIoAxIYChBiYXR0bGVPd25lckRjZ2lk
GAIgAigDEhIKCnR1cm5zQ291bnQYAyACKAUSVwoOb3Bwb25lbnRTdGF0dXMYBCACKA4yPy5pdHV4d2Fycy5TZXJ2ZXJSZXNwb25z
ZS5HZXRCYXR0bGVTdGF0dXNSZXNwb25zZS5PcHBvbmVudFN0YXR1cyI6Cg5PcHBvbmVudFN0YXR1cxILCgdPRkZMSU5FEAASCgoG
T05MSU5FEAESDwoLUExBWUlOR19OT1cQAhoWChRSZXNlcnZlTWF0Y2hSZXNwb25zZRocChpTYXZlRmlyc3RUaW1lU3RhdGVSZXNw
b25zZRrRAgoVR2V0Q3VzdG9taXplclJlc3BvbnNlEi4KDWN1c3RvbUNvbnRlbnQYASACKAsyFy5pdHV4d2Fycy5DdXN0b21Db250
ZW50EhEKCWF2YWlsYWJsZRgCIAIoCBIsCgxwb3B1cENvbnRlbnQYAyABKAsyFi5pdHV4d2Fycy5Qb3B1cENvbnRlbnQSFwoPY3Vz
dG9tQXZhaWxhYmxlGAQgASgIEhYKDnBvcHVwQXZhaWxhYmxlGAUgASgIEkoKDXBjUHJpY2Vwb2ludHMYBiADKAsyMy5pdHV4d2Fy
cy5TZXJ2ZXJSZXNwb25zZS5Mb2dpblJlc3BvbnNlLlBDUHJpY2Vwb2ludBJKCg1nY1ByaWNlcG9pbnRzGAcgAygLMjMuaXR1eHdh
cnMuU2VydmVyUmVzcG9uc2UuTG9naW5SZXNwb25zZS5HQ1ByaWNlcG9pbnQaFQoTUmVwb3J0RXJyb3JSZXNwb25zZRqnAQodQ3Jl
YXRlQmF0dGxlVXNpbmdOaWNrUmVzcG9uc2USDwoHc3VjY2VzcxgBIAIoCBIvCgZiYXR0bGUYAiABKAsyHy5pdHV4d2Fycy5TZXJ2
ZXJSZXNwb25zZS5CYXR0bGUSFQoNb3Bwb25lbnREY2dpZBgDIAEoAxIUCgxvcHBvbmVudE5pY2sYBCABKAkSFwoPb3Bwb25lbnRQ
aWN0dXJlGAUgASgJGhkKF0FkZEluR2FtZUZyaWVuZFJlc3BvbnNlGiEKH1JlcG9ydEFjaGlldmVtZW50U3RhdHVzUmVzcG9uc2Ua
RAogQ29sbGVjdEFjaGlldmVtZW50UmV3YXJkUmVzcG9uc2USDwoHdG90YWxQQxgBIAIoBRIPCgd0b3RhbEdDGAIgAigFGlAKFUdl
dENvbmZpZ0RhdGFSZXNwb25zZRIPCgd2ZXJzaW9uGAEgAigJEhEKCWNvbmZpZ1VybBgCIAIoCRITCgtyZXNvdXJjZVVybBgDIAIo
CRpiChxHZXROZXh0T3duVHVybkJhdHRsZVJlc3BvbnNlEhEKCWF2YWlsYWJsZRgBIAIoCBIvCgZiYXR0bGUYAiABKAsyHy5pdHV4
d2Fycy5TZXJ2ZXJSZXNwb25zZS5CYXR0bGUabwoaUGF5bWVudElvc0Zvckl0ZW1zUmVzcG9uc2USDwoHc3VjY2VzcxgBIAIoCBIV
Cg10cmFuc2FjdGlvbklkGAMgASgJEhUKDWl0ZW1zVW5sb2NrZWQYBCACKAgSEgoKaXNSZXN0b3JlZBgFIAIoCCKDAQoSU2VydmVy
UmVzcG9uc2VDb2RlEgYKAk9LEAASFQoRSU5WQUxJRF9TSUdOQVRVUkUQARIPCgtPVVRfT0ZfU1lOQxACEhMKD0lOVkFMSURfQ09V
TlRFUhADEhQKEEVSUk9SX0lOX1NFUlZJQ0UQBBISCg5JTlRFUk5BTF9FUlJPUhAFIlsKFVNlcnZlclJlc3BvbnNlV3JhcHBlchIV
Cg1hdXRoZW50aWNhdGVkGAEgAigIEhcKD3NlcnZlclJlc3BvbnNlcxgCIAMoDBISCgpzaWduYXR1cmVzGAMgAygMIoACCg1DdXN0
b21Db250ZW50Ei0KBnRhYmxlcxgBIAMoCzIdLml0dXh3YXJzLkN1c3RvbUNvbnRlbnQuVGFibGUaRQoFVGFibGUSEQoJdGFibGVO
YW1lGAEgAigJEikKBHJvd3MYAiADKAsyGy5pdHV4d2Fycy5DdXN0b21Db250ZW50LlJvdxpNCgNSb3cSDQoFcm93SWQYASACKAkS
NwoJb3ZlcnJpZGVzGAIgAygLMiQuaXR1eHdhcnMuQ3VzdG9tQ29udGVudC5PdmVycmlkZVBhaXIaKgoMT3ZlcnJpZGVQYWlyEgsK
A2tleRgBIAIoCRINCgV2YWx1ZRgCIAIoCSJgChVEYXRhYmFzZUN1c3RvbUNvbnRlbnQSLgoNY3VzdG9tQ29udGVudBgBIAIoCzIX
Lml0dXh3YXJzLkN1c3RvbUNvbnRlbnQSFwoPZGVsaXZlcmVkVG9Vc2VyGAIgAigIIicKCUF0dHJpYnV0ZRILCgNrZXkYASACKAkS
DQoFdmFsdWUYAiACKAki4QMKDFBvcHVwQ29udGVudBIvCgdjb250ZW50GAEgAygLMh4uaXR1eHdhcnMuUG9wdXBDb250ZW50LkNv
bnRlbnQanwMKB0NvbnRlbnQSJgoJYXR0cmlidXRlGAEgAygLMhMuaXR1eHdhcnMuQXR0cmlidXRlEkEKDGFjdGlvbkJ1dHRvbhgC
IAMoCzIrLml0dXh3YXJzLlBvcHVwQ29udGVudC5Db250ZW50LkFjdGlvbkJ1dHRvbhqoAgoMQWN0aW9uQnV0dG9uEiYKCWF0dHJp
YnV0ZRgBIAMoCzITLml0dXh3YXJzLkF0dHJpYnV0ZRJGCgh0cmFja2luZxgCIAMoCzI0Lml0dXh3YXJzLlBvcHVwQ29udGVudC5D
b250ZW50LkFjdGlvbkJ1dHRvbi5UcmFja2luZxJCCgZwYXJhbXMYAyADKAsyMi5pdHV4d2Fycy5Qb3B1cENvbnRlbnQuQ29udGVu
dC5BY3Rpb25CdXR0b24uUGFyYW1zGjIKCFRyYWNraW5nEiYKCWF0dHJpYnV0ZRgBIAMoCzITLml0dXh3YXJzLkF0dHJpYnV0ZRow
CgZQYXJhbXMSJgoJYXR0cmlidXRlGAEgAygLMhMuaXR1eHdhcnMuQXR0cmlidXRlIkQKFERhdGFiYXNlUG9wdXBDb250ZW50EiwK
DHBvcHVwQ29udGVudBgBIAIoCzIWLml0dXh3YXJzLlBvcHVwQ29udGVudCKxCQoMRGF0YWJhc2VVc2VyEg0KBWRjZ2lkGAEgAigD
EiAKEXR1dG9yaWFsQ29tcGxldGVkGAIgAigIOgVmYWxzZRITCgtnYW1lU2Vzc2lvbhgDIAIoCRIZChFuaWNrQ2hhbmdlQ291bnRl
chgEIAIoBRIMCgRuaWNrGAUgAigJEgwKBGNhc2gYBiACKAMSDQoFY29pbnMYByACKAUSDQoFc2NvcmUYCCACKAMSHAoUbGFzdE5v
dGlmaWNhdGlvblNlbnQYCyABKAMSDwoHY291bnRlchgMIAIoBRIQCgh0aW1lem9uZRgNIAEoBRIZChFsYXN0UmV3YXJkZWRMZXZl
bBgOIAIoBRIQCgh3aW5Db3VudBgPIAIoBRISCgptYXRjaENvdW50GBsgAigFEhEKCXR1cm5Db3VudBgcIAIoBRIUCgxjcmVhdGlv
blRpbWUYHSACKAMSPAoOaW52ZW50b3J5SXRlbXMYCSADKAsyJC5pdHV4d2Fycy5EYXRhYmFzZVVzZXIuSW52ZW50b3J5SXRlbRIr
CiNkaXNhYmxlZFB1c2hOb3RpZmljYXRpb25DYXRlZ29yeUlkcxgKIAMoBRIgChhpb3NQYXltZW50VHJhbnNhY3Rpb25JZHMYECAD
KAkSLwoMcmF0aW5nU3RhdHVzGBEgASgOMhkuaXR1eHdhcnMuQXBwUmF0aW5nU3RhdHVzEiAKGHJlbWFpbmluZ1ZpY3Rvcmllc1Rv
UmF0ZRgSIAEoBRIPCgd2ZXJzaW9uGBMgASgFEhkKEWlNQlBsYXRmb3JtVXNlcklkGBQgASgJEhcKD2xhc3RSZXF1ZXN0VGltZRgV
IAEoAxIgChhsYXN0R2V0QmF0dGxlUmVxdWVzdFRpbWUYFiABKAMSJAocbGFzdEdldEJhdHRsZVJlcXVlc3RCYXR0bGVJZBgXIAEo
AxIWCg5maXJzdFRpbWVTdGF0ZRgYIAEoBRIXCg9jcm1SZXdhcmRzQ29pbnMYHiABKAUSFgoOY3JtUmV3YXJkc0Nhc2gYHyABKAUS
EAoIdGVzdFVzZXIYICABKAgSNAoKc2F2ZWRVc2VycxghIAMoCzIgLml0dXh3YXJzLkRhdGFiYXNlVXNlci5TYXZlZFVzZXISMAoO
dXNlclN0YXRpc3RpY3MYIiABKAsyGC5pdHV4d2Fycy5Vc2VyU3RhdGlzdGljcxIdChVuZWVkVG9Eb3VibGVQY09uZVRpbWUYIyAB
KAgSPwoNcG9wdXBEZWxpdmVyeRgkIAMoCzIoLml0dXh3YXJzLkRhdGFiYXNlVXNlci5Qb3B1cERlbGl2ZXJ5RGF0YRIhChlwdXJj
aGFzZWROb25jb25zdW1hYmxlSWRzGCYgAygJGkAKDUludmVudG9yeUl0ZW0SDgoGaXRlbUlkGAEgAigJEg0KBWNvdW50GAIgAigF
EhAKCGlzTG9ja2VkGAMgASgIGigKCVNhdmVkVXNlchINCgVkY2dpZBgBIAIoAxIMCgRuaWNrGAIgAigJGjwKEVBvcHVwRGVsaXZl
cnlEYXRhEhEKCWNvbnRlbnRJZBgBIAIoCRIUCgxkZWxpdmVyeVRpbWUYAiACKAMiqwIKDlVzZXJTdGF0aXN0aWNzEjoKCGNvdW50
ZXJzGAEgAygLMiguaXR1eHdhcnMuVXNlclN0YXRpc3RpY3MuRGF0YWJhc2VDb3VudGVyEhwKFHJld2FyZGVkQWNoaWV2ZW1lbnRz
GAIgAygJEkMKEGZyaWVuZFN0YXRpc3RpY3MYAyADKAsyKS5pdHV4d2Fycy5Vc2VyU3RhdGlzdGljcy5GcmllbmRTdGF0aXN0aWNz
EhQKDGxldmVsc1BsYXllZBgEIAMoCRotCg9EYXRhYmFzZUNvdW50ZXISCwoDa2V5GAEgAigJEg0KBXZhbHVlGAIgAigFGjUKEEZy
aWVuZFN0YXRpc3RpY3MSDQoFZGNnaWQYASACKAMSEgoKd29uQWdhaW5zdBgCIAIoBSKwAgoORGF0YWJhc2VDb25maWcSHAoUbWF0
Y2hNYWtlck1heFdhaXRlcnMYASACKAUSTwoWbWF0Y2hNYWtlcldlaWdodENvbmZpZxgCIAMoCzIvLml0dXh3YXJzLkRhdGFiYXNl
Q29uZmlnLk1hdGNoTWFrZXJXZWlnaHRDb25maWcSPwoPZmVhdHVyZVN0YXR1c2VzGAMgAygLMiYuaXR1eHdhcnMuRGF0YWJhc2VD
b25maWcuRmVhdHVyZVN0YXR1cxo7ChZNYXRjaE1ha2VyV2VpZ2h0Q29uZmlnEhEKCWRpbWVuc2lvbhgBIAIoBRIOCgZ3ZWlnaHQY
AiACKAEaMQoNRmVhdHVyZVN0YXR1cxIPCgdmZWF0dXJlGAEgAigJEg8KB2VuYWJsZWQYAiACKAgi/gEKGkZpbmRNYXRjaFJlcXVl
c3RTZXJ2ZXJTaWRlEjcKBG1vZGUYASACKA4yKS5pdHV4d2Fycy5GaW5kTWF0Y2hSZXF1ZXN0U2VydmVyU2lkZS5Nb2RlEg0KBWRj
Z2lkGAIgAigDEjYKEW1hdGNoTWFrZXJNZXRyaWNzGAMgAigLMhsuaXR1eHdhcnMuTWF0Y2hNYWtlck1ldHJpY3MSEAoIYmF0dGxl
SWQYCCABKAMSGAoQbWluUmVxdWlyZWRMZXZlbBgJIAEoBSI0CgRNb2RlEgoKBk5PUk1BTBABEg8KC0ZPUkNFX1NUQVJUEAISDwoL
Rk9SQ0VfUVVFVUUQAyLNAQobRmluZE1hdGNoUmVzcG9uc2VTZXJ2ZXJTaWRlElIKEW1hdGNoUmVzcG9uc2VUeXBlGAEgAigOMjcu
aXR1eHdhcnMuRmluZE1hdGNoUmVzcG9uc2VTZXJ2ZXJTaWRlLk1hdGNoUmVzcG9uc2VUeXBlEhUKDW9wcG9uZW50RGNnaWQYAiAB
KAMSEAoIYmF0dGxlSWQYAyABKAMiMQoRTWF0Y2hSZXNwb25zZVR5cGUSCwoHV0FJVElORxAAEg8KC01BVENIX0ZPVU5EEAEiegoe
TU1RdWV1ZVN0YXR1c1JlcXVlc3RTZXJ2ZXJTaWRlEg0KBWRjZ2lkGAEgAigDEjYKEW1hdGNoTWFrZXJNZXRyaWNzGAMgASgLMhsu
aXR1eHdhcnMuTWF0Y2hNYWtlck1ldHJpY3MSEQoJYmF0dGxlSWRzGAogAygDIjIKH01NUXVldWVTdGF0dXNSZXNwb25zZVNlcnZl
clNpZGUSDwoHaW5RdWV1ZRgBIAIoCCI/Ch1SZXNlcnZlTWF0Y2hSZXF1ZXN0U2VydmVyU2lkZRIPCgdyZXNlcnZlGAEgAigIEg0K
BWRjZ2lkGAIgAigDIkEKHFJlbW92ZU1hdGNoUmVxdWVzdFNlcnZlclNpZGUSDwoHb3duZXJJZBgBIAIoAxIQCghiYXR0bGVJZBgC
IAIoAyIzCh1SZW1vdmVNYXRjaFJlc3BvbnNlU2VydmVyU2lkZRISCgp3YXNQcmVzZW50GAEgAigIImsKEU1hdGNoTWFrZXJNZXRy
aWNzEg0KBWxldmVsGAMgAigFEhMKC3R1cm5zUGVyRGF5GAQgAigBEhAKCHRpbWV6b25lGAUgAigFEhEKCWVxdWlwbWVudBgGIAIo
BRINCgVza2lsbBgHIAIoASLRAQoPTWF0Y2hNYWtlclF1ZXVlEk4KFW1hdGNoTWFrZXJCYXR0bGVFbnRyeRgBIAMoCzIvLml0dXh3
YXJzLk1hdGNoTWFrZXJRdWV1ZS5NYXRjaE1ha2VyQmF0dGxlRW50cnkabgoVTWF0Y2hNYWtlckJhdHRsZUVudHJ5Eg8KB293bmVy
SWQYASACKAMSEAoIYmF0dGxlSWQYAiACKAMSGAoQbWluUmVxdWlyZWRMZXZlbBgDIAIoBRIYChBtYXRjaE1ha2VyTWV0cmljGAUg
AygBIuwHCg5EYXRhYmFzZUJhdHRsZRIKCgJpZBgBIAIoAxIqCgtiYXR0bGVTdGF0ZRgCIAIoDjIVLml0dXh3YXJzLkJhdHRsZVN0
YXRlEiwKDmxhc3RCYXR0bGVUdXJuGAMgASgLMhQuaXR1eHdhcnMuQmF0dGxlVHVybhIYChBsYXN0QmF0dGxlVHVybkF0GAQgAigD
EhcKD2JhdHRsZVR1cm5Db3VudBgFIAIoBRINCgVsZXZlbBgGIAIoCRIZChFiYXR0bGVXaW5uZXJEY2dpZBgHIAEoAxISCgpvd25l
ckRjZ2lkGAsgAigDEhEKCW93bmVyTmFtZRgMIAIoCRIUCgxvd25lclBpY3R1cmUYDSACKAkSGwoTb3duZXJGYWNlYm9va1VzZXJJ
ZBgOIAEoCRIdChVvd25lckdhbWVDZW50ZXJVc2VySWQYDyABKAkSFgoOb3duZXJLaWxsQ291bnQYECACKAUSGAoQb3duZXJEYW1h
Z2VQcm9wcxgRIAIoBRIcChRvd25lckRhbWFnZUhpdFBvaW50cxgSIAIoBRISCgpvd25lclNjb3JlGBMgASgFEhgKEG93bmVyTGFz
dE51ZGdlQXQYFCABKAMSGgoSb3duZXJEZWxldGVkQmF0dGxlGB8gASgIEhsKE293bmVyTGFzdFVzZWRXZWFwb24YICABKAkSGwoT
b3duZXJVc2VkU2FtZVdlYXBvbhghIAEoCBIVCg1vcHBvbmVudERjZ2lkGBUgAigDEhQKDG9wcG9uZW50TmFtZRgWIAIoCRIXCg9v
cHBvbmVudFBpY3R1cmUYFyACKAkSHgoWb3Bwb25lbnRGYWNlYm9va1VzZXJJZBgYIAEoCRIgChhvcHBvbmVudEdhbWVDZW50ZXJV
c2VySWQYGSABKAkSGQoRb3Bwb25lbnRLaWxsQ291bnQYGiACKAUSGwoTb3Bwb25lbnREYW1hZ2VQcm9wcxgbIAIoBRIfChdvcHBv
bmVudERhbWFnZUhpdFBvaW50cxgcIAIoBRIVCg1vcHBvbmVudFNjb3JlGB0gASgFEhsKE29wcG9uZW50TGFzdE51ZGdlQXQYHiAB
KAMSHQoVb3Bwb25lbnREZWxldGVkQmF0dGxlGCkgASgIEh4KFm9wcG9uZW50TGFzdFVzZWRXZWFwb24YKiABKAkSHgoWb3Bwb25l
bnRVc2VkU2FtZVdlYXBvbhgrIAEoCBIXCg9pc0R1bW15T3Bwb25lbnQYMiABKAgSEQoJaXNSZW1hdGNoGDMgASgIEhQKDGFyZUZi
RnJpZW5kcxg0IAEoCBIUCgxhcmVHY0ZyaWVuZHMYNSABKAgi0wIKFURhdGFiYXNlUGF5bWVudFJlY29yZBINCgVkY2dpZBgBIAIo
AxIVCg10cmFuc2FjdGlvbklkGAIgASgJEj0KBnN0YXR1cxgDIAIoDjItLml0dXh3YXJzLkRhdGFiYXNlUGF5bWVudFJlY29yZC5Q
YXltZW50U3RhdHVzEhEKCXBhY2thZ2VJZBgEIAIoCRIRCgl0aW1lc3RhbXAYBSACKAMSDwoHcGNBZGRlZBgGIAIoBRIPCgdnY0Fk
ZGVkGAcgAigFEhAKCHZlcmlmaWVkGAggASgIEg8KB3NhbmRib3gYCSABKAgSGQoRYWxsV2VhcG9uVW5sb2NrZWQYCiABKAgiTwoN
UGF5bWVudFN0YXR1cxIMCghBTExfR09PRBAAEhcKE1NBTUVfVFJBTlNBQ1RJT05fSUQQARIXChNWRVJJRklDQVRJT05fRkFJTEVE
EAIqkAYKEVNlcnZlclJlcXVlc3RUeXBlEhIKBUVSUk9SEP///////////wESDQoJQlVZX0NPSU5TEBUSDAoIQlVZX0lURU0QARIP
CgtDSEFOR0VfTklDSxACEgkKBUNIRUNLEAMSDgoKQ0hFQ0tfTklDSxAEEhUKEUNPTVBMRVRFX1RVVE9SSUFMEAUSEgoOQ1JFQVRF
X0FDQ09VTlQQBhIRCg1DUkVBVEVfQkFUVExFEAcSDgoKRklORF9NQVRDSBAIEiIKHkdBTUVfQ0VOVEVSX1VTRVJfSURTX1RPX0RD
R0lEUxASEg4KCkdFVF9CQVRUTEUQCRIMCghMRVZFTF9VUBATEgkKBUxPR0lOEAoSDwoLUEFZTUVOVF9JT1MQFBIUChBQT0xMX0JB
VFRMRV9MSVNUEAsSEQoNU0VORF9SRU1JTkRFUhAREiAKHFNFVF9QVVNIX05PVElGSUNBVElPTl9TVEFUVVMQDBIWChJTVUJNSVRf
QkFUVExFX1RVUk4QDhIXChNVUERBVEVfREVWSUNFX1RPS0VOEA8SGwoXVVBEQVRFX0dBTUVfQ0VOVEVSX0lORk8QEBIYChRVUERB
VEVfUkFUSU5HX1NUQVRVUxAWEhEKDURFTEVURV9CQVRUTEUQFxIVChFHRVRfQkFUVExFX1NUQVRVUxAYEhEKDVJFU0VSVkVfTUFU
Q0gQGRIZChVTQVZFX0ZJUlNUX1RJTUVfU1RBVEUQGhISCg5HRVRfQ1VTVE9NSVpFUhAbEhAKDFJFUE9SVF9FUlJPUhAcEhwKGENS
RUFURV9CQVRUTEVfVVNJTkdfTklDSxAdEhYKEkFERF9JTl9HQU1FX0ZSSUVORBAeEh0KGVJFUE9SVF9BQ0hJRVZFTUVOVF9TVEFU
VVMQHxIeChpDT0xMRUNUX0FDSElFVkVNRU5UX1JFV0FSRBAgEhMKD0dFVF9DT05GSUdfREFUQRAhEhwKGEdFVF9ORVhUX09XTl9U
VVJOX0JBVFRMRRAiEhkKFVBBWU1FTlRfSU9TX0ZPUl9JVEVNUxAjKjIKFFNlcnZlclJlcXVlc3RDaGFubmVsEgsKB09SREVSRUQQ
ARINCglVTk9SREVSRUQQAipICg9BcHBSYXRpbmdTdGF0dXMSEQoNTk9UX1lFVF9SQVRFRBAAEgkKBVJBVEVEEAESFwoTQ0xPU0VE
X1JBVElOR19QT1BVUBACKlEKC0JhdHRsZVN0YXRlEgsKB09OR09JTkcQABIMCghGSU5JU0hFRBABEggKBFFVSVQQAxILCgdFWFBJ
UkVEEAQSEAoMRklOSVNIRURfQUNLEAVCJwoXY29tLmRjaG9jLml0dXh3YXJzLmRhdGFCDGlUdXhXYXJzRGF0YQ==
"""

# ---------------------------------------------------------------- protobuf setup
_fdp = descriptor_pb2.FileDescriptorProto()
_fdp.ParseFromString(base64.b64decode("".join(_DESC_B64.split())))
_pool = descriptor_pool.DescriptorPool()
_pool.Add(_fdp)
if GetMessageClass:
    def M(name):
        return GetMessageClass(_pool.FindMessageTypeByName("ituxwars." + name))
else:
    _factory = MessageFactory(_pool)
    def M(name):
        return _factory.GetPrototype(_pool.FindMessageTypeByName("ituxwars." + name))

ReqWrapper, RespWrapper = M("ServerRequestWrapper"), M("ServerResponseWrapper")
Req, Resp = M("ServerRequest"), M("ServerResponse")
TYPE_ENUM = _pool.FindEnumTypeByName("ituxwars.ServerRequestType")
TYPE_NAME = {v.number: v.name for v in TYPE_ENUM.values}

# ---------------------------------------------------------------- helpers
def camel(type_name):  # "GET_CONFIG_DATA" -> "getConfigData"
    p = type_name.lower().split("_")
    return p[0] + "".join(x.title() for x in p[1:])

def _is_required(f):
    # protobuf >= 6.x exposes is_required; older versions only have .label
    r = getattr(f, "is_required", None)
    if r is not None:
        return bool(r)
    return f.label == f.LABEL_REQUIRED

def fill_required(msg):
    """Give every unset required field a harmless default (recursively)."""
    for f in msg.DESCRIPTOR.fields:
        if not _is_required(f):
            continue
        if f.type == f.TYPE_MESSAGE:
            sub = getattr(msg, f.name)
            sub.SetInParent()
            fill_required(sub)
        elif not msg.HasField(f.name):
            if f.type == f.TYPE_ENUM:
                setattr(msg, f.name, f.enum_type.values[0].number)
            else:
                setattr(msg, f.name, f.default_value)

def sign(payload, session):
    return hashlib.md5(payload + session.encode() + SECRET).digest()

def session_for(dcgid):
    return "session-%d" % dcgid

def log(*a):
    line = " ".join(str(x) for x in a)
    print(line, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")

# ---------------------------------------------------------------- tiny user store
users = {}
if os.path.exists(DB_FILE):
    try:
        users = {int(k): v for k, v in json.load(open(DB_FILE)).items()}
    except Exception:
        users = {}

def save_users():
    json.dump(users, open(DB_FILE, "w"), indent=1)

def get_user(dcgid=None):
    if not dcgid or dcgid not in users:
        dcgid = dcgid or (max(users) + 1 if users else 1000001)
        users[dcgid] = dict(dcgid=dcgid, nick="Penguin%d" % (dcgid % 10000), cash=START_CASH,
                    coins=START_COINS, score=0, first=FIRST_TIME_STATE,
                    items=dict(START_ITEMS))
        save_users()
    return users[dcgid]

# ---------------------------------------------------------------- request handlers
def handle(req, resp):
    """Fill the typed response sub-message for one request. Returns the dcgid in play."""
    t = TYPE_NAME.get(req.serverRequestType, "UNKNOWN")
    sub_name = camel(t) + "Response"
    sub = getattr(resp, sub_name, None) if t != "UNKNOWN" else None
    dcgid = req.dcgid if req.HasField("dcgid") else None

    if sub is None:
        return dcgid
    sub.SetInParent()

    if t == "CHECK":
        sub.serverVersion = req.checkRequest.version
        sub.serverMinimumVersion = 0
        sub.invalidVersionMessage = ""
        sub.hotChocolateMessage = ""
    elif t in ("CREATE_ACCOUNT", "LOGIN"):
        u = get_user(dcgid)
        sub.dcgid = u["dcgid"]
        sub.gameSession = session_for(u["dcgid"])
        sub.nick = u["nick"]
        dcgid = u["dcgid"]
        if t == "LOGIN":
            sub.cash, sub.coins, sub.score = u["cash"], u["coins"], u["score"]
            sub.tutorialCompleted = bool(u.get("tutorial_done", False))
            sub.canChangeNick = True
            sub.syncEnabled = False           # no cash/coins/score sync checks
            sub.firstTimeState = u["first"]
            sub.achievementData.SetInParent()
            for iid, cnt in u.setdefault("items", dict(START_ITEMS)).items():
                it = sub.inventoryItems.add()
                it.itemId, it.count = iid, cnt
    elif t == "CHECK_NICK":
        sub.ok = True
    elif t == "SAVE_FIRST_TIME_STATE":
        u = get_user(dcgid); u["first"] = req.saveFirstTimeStateRequest.state; save_users()
    elif t == "GET_CUSTOMIZER":
        sub.customContent.SetInParent()
        sub.available = False
    elif t == "GET_CONFIG_DATA":
        sub.version, sub.configUrl, sub.resourceUrl = "", "", ""
    elif t == "POLL_BATTLE_LIST":
        sub.battles.SetInParent()
    elif t == "COMPLETE_TUTORIAL":
        u = get_user(dcgid)
        r = req.completeTutorialRequest
        u["cash"], u["coins"] = r.cash, r.coins
        u["items"] = {i.itemId: i.count for i in r.inventoryItems} or u.get("items", dict(START_ITEMS))
        u["tutorial_done"] = True
        save_users()
    fill_required(sub)
    return dcgid

# ---------------------------------------------------------------- HTTP
app = Flask(__name__)

@app.route("/", defaults={"path": ""}, methods=["GET", "POST"])
@app.route("/<path:path>", methods=["GET", "POST"])
def endpoint(path):
    if request.method == "GET":
        return "Penguin Wars server is up", 200
    body = request.get_data()
    if body[:2] == b"\x1f\x8b":
        body = gzip.decompress(body)
    log("\n=== %s POST /%s (%d bytes)" % (time.strftime("%H:%M:%S"), path, len(body)))
    wrapper = ReqWrapper()
    try:
        wrapper.ParseFromString(body)
    except Exception as e:
        log("!! could not parse body as ServerRequestWrapper:", e, body[:64].hex())
        return Response(b"", 400)

    out = RespWrapper()
    out.authenticated = True
    for i, raw in enumerate(wrapper.serverRequests):
        req = Req(); req.ParseFromString(raw)
        sig = wrapper.signatures[i] if i < len(wrapper.signatures) else b""
        # work out which gameSession the client signed with (so we can sign our reply the same way)
        cands = [""]
        if req.HasField("dcgid"):
            cands.insert(0, session_for(req.dcgid))
        session = next((c for c in cands if sign(raw, c) == sig), None)
        log("-- request %d: %s  sig %s" % (i, TYPE_NAME.get(req.serverRequestType), "OK" if session is not None else "MISMATCH (continuing)"))
        log(text_format.MessageToString(req, as_utf8=True).rstrip())
        if session is None:
            session = cands[0]

        resp = Resp()
        resp.serverRequestType = req.serverRequestType
        resp.serverRequestChannel = req.serverRequestChannel
        resp.responseCode = 0   # OK
        if req.HasField("counter"):
            resp.counter = req.counter
        dcgid = handle(req, resp)
        payload = resp.SerializeToString()
        # the client verifies with whatever gameSession it holds *before* applying this response
        out.serverResponses.append(payload)
        out.signatures.append(sign(payload, session))
        log("<< response:\n" + text_format.MessageToString(resp, as_utf8=True).rstrip())
    return Response(out.SerializeToString(), mimetype="application/x-protobuf")

if __name__ == "__main__":
    log("listening on http://%s:%d  (set ServerUrl to <this-pc-ip>:%d)" % (HOST, PORT, PORT))
    app.run(host=HOST, port=PORT, debug=True, threaded=False)