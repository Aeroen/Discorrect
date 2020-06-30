Dyscordia
=====

### Simple Python script to massively shred the messages sent on a Discord channel 

Such a script is able to control your Discord account as a whole. Therefore, several parameters are required (including your Discord token) while some others are optional and can be used in order to somewhat imitate how the desktop client works.   
If you don't know how and where said parameters can be found, you're probably unable to check whether or not this script will send your data to a malicious server. In such a case, please do yourself a favor and don't use it.

Using Dyscordia might be against Discord's Terms of Service, I don't know, I haven't read those.  
This script is provided as is, without any warranty of any kind, etc; if you use it and get banned or anything else, I won't be held responsible.


### Dependencies

- requests : `pip3 install --user requests`  


### Awesome Q&A

Q: Wtf is this name?  
A: Discord + Dystopia. Thanks for asking, hope it's been worthwhile!  

Q: How does it work?  
A: Each message from a specified channel is overwritten, then deleted. Every action is followed by a short pause for obvious reasons.  

Q: Why would you overwrite before deletion?  
A: Discord doesn't delete anything, it only stops being visible. Thanks to GDPR, you can verify this statement by [asking for your data](https://support.discord.com/hc/en-us/articles/360004027692).
