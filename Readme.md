Discorrect
=====

### Disclaimer

Such a script is able to control your Discord account as a whole. Therefore, several parameters are required (including your Discord token) while some others are optional and can be used in order to somewhat imitate how the desktop client works.   
If you don't know how and where said parameters can be found, you're probably unable to check whether or not this script is going to send your data to a malicious server. In such a case, please do yourself a favor and don't use it.

Using Discorrect might be against Discord's Terms of Service, I don't know, I haven't read those.  
This script is provided as is, without any warranty of any kind, etc; if you use it and get banned or anything else, I won't be held responsible.


### Dependencies

- requests : `pip3 install --user requests`  


### Q&A

Q: How does it work?  
A: Each message from a specified channel is overwritten, then deleted. Every action is followed by a short pause for obvious reasons.  

Q: Why would you overwrite before deletion?  
A: Officially, deleted messages are also deleted server-side. However, since Discord is proprietary software, there is no way to review its source code: we can only rely on their word. Blind trust should be avoided as much as possible whenever dealing about privacy, hence this choice was made.  

Q: Yeah, I don't care. How can I delete my messages as fast as possible, without overwriting?  
A: Use the `-d` or `--dont-overwrite` flag to disable overwriting. Maybe `-s 3` or `--speed 3` as well, that's up to you.  
