<p align="center">
  <img src="static/img/remotely.png">
</p>

### What is Remotely?

[Remotely](http://www.remotely.coffee/) is a web app developed to help you (remote worker or traveler) find the best coffee shop to work from.    
It uses your input and matches it to coffee shops based on reviews by previous customers. Natural language processing helps determine which locations you might like. More specifically, the app uses a word2vec model to find the coffeeshops most similar to your input.    

Currently, the app only works for New York City, but it will be scaled to other cities in the future!

The app's components:

1. app.py file
  - Has all the functions to run the app
  - Routes (through @app.route) to pages and specifies what templates to use with render_template()
  - At the end this makes sure it runs:  
```  
  if __name__ == '__main__':
      app.run(host='0.0.0.0', port=8080, debug=True)
```

2. .html files in templates folder (to specify how the pages look and what data and functions are passed through the app.)
  - index.html is the home page
  - recommender.html is the form the user fills out
  - recommendations.html does the bulk of the work, passing the user input through the recommender function and outputting the recommendation

3. the static folder has images, fonts, css, etc. Other Bootstrap templates can be downloaded to make the app look better: (https://getbootstrap.com/docs/4.1/examples/)
