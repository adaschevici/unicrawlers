gente
=====

Upgraded to version 0.22 scrapy.

How it works:

You have an UI inside the ui dir which is a simple flask front end.

On the back end there is a scrapyd server that the spiders are deployed to.
To run spiders on this scrapyd server you have to have the spiders eggified, which can be handled via

scrapyd-deploy default -p spider

default is the name of the scrapyd server

spider is the name of the project


