<b> Need something new to read? </b>
-
<p>This web application helps users to find books within their realm of interest, after the user rates a few books they've already read! If you only want to see a visual demonstration, please feel free to skip the following jargon and scroll down to the <b> Visual Demonstration </b> section to view some GIFs.</p>


Note -- This repository does not contain all the necessary files to run the application, as some are much too large to store on GitHub! It merely contains all files that I've hand written (i.e. the source code), and is simply a means for me to demonstrate how the application runs. In the visual demonstration, I run the application on a Debian Linux operating system, with a Firefox client browser, Apache webserver and a MariaDB (MySQL) database. A classic LAMP setup!

<b> A General Technical Description -- Backend </b>
-
Written in Python, the system combines a variety of machine learning recommendation methods, including:
- Matrix factorization (Collaborative filtering)
    - A pool of candidate books and authors are collected (see the following bulletpoints) and scored according to how likely the system predicts a user will enjoy a book/author.
    - The scoring is calculated collectively from an existing userbase of over 6,000 users and over 250,000 ratings. 
      - You can view the original dataset here: https://www.kaggle.com/ruchi798/bookcrossing-dataset. To make the dataset usable, I've had to do extensive cleaning, so the original is much larger.
    - Only the books/authors with the greatest predicted score are shown to the user as the final output.
    - The particular algorithm I use here is Alternating Least Squares (ALS), provided by a Python library known as Implicit.

- Item-item similarity (Content-based filtering)
    - A similarity measure between the user's items and other items is calculated, and only the most similar items are considered for overall scoring.
    - To measure similarity, both a SciKit-learn implementation of cosine-similarity is used, as well as in-built utilities in Implicit.

- User-user similarity (Content-based filtering)
    - Like item-item similarity, a similarity measure is instead calculated between the user and other users. Only the interests of the most similar users are thus considered for overall scoring.
    - Both SciKit-learn cosine-similarity and in-built Implicit utilities are used for the calculation.
    
 Addressing the recommendation cold-start problem: the system generically recommends the most popular books across the entire dataset, and hence such a recommendation is not personalized. I've stipulated that only after some number <i>N</i> ratings the user has given, the system will begin to personalize to the user.
 
For execution speed, the most up-to-date model is cached for quick recommendations. For the system to yield fresh recommendations from new ratings however, the entire model must be re-trained. Unfortunately, this process is by far the most time consuming in the system. In the visual demonstration, I only show asynchronous online model re-trainings after the user provides a set of new ratings. In a live deployment however, the server will ideally constantly re-train and update the system offline when the user is not logged in.

<b> A General Technical Description -- Frontend </b>
-
A web-exclusive application, written in ReactJS (hooks!) and partially with Bootstrap 4 on the client, along with PHP on the server-side, I designed this frontend mostly with flashiness and fun in mind first, and usability second. The choice to do so is not out of necessity! I could've built a more traditional, boring user-interface, but I figure doing something out of the box would be a bit more interesting and useful to show off what I can do. As a result, while I originally planned to keep mostly to a CSS framework like Bootstrap, I gradually used my own code as these frameworks are too restrictive for what I wanted to do.

The style is quite minimalist, and the focal point is a simple carousel in the center of the screen. The user can manipulate what is being displaying on the carousel, via buttons on the navigation bar. A carousel was used for all information simply to re-use code. The user-interface has several utilities, including:

- Navigation bar
  - The user's main tool to manipulate what is shown on screen.
  - Buttons differ depending on if the user is logged in or logged out.
  - Passively shows a 'loading message' indicating that the model is being asynchronously re-trained and recommendations will appear soon. Upon completion, the user is notified and the recommendations are updated.

- Loading and landing screens
  - What a user initially sees are unpersonalized generic recommendations of popular items.
  - These are randomized on the server, and thus the client needs a bit of time to receive a reply. This is hidden with a very brief loading/splash screen.
  ![](gifs/landing.gif)
  
- User login/logout and registration
  - Very minimalist, but contains all the client-end form verification needed to ensure proper authentication.
  - The user is notified of badly given input, failed authentication, and existing accounts.
  - Upon successful registration, the user is automatically logged in, just for simplicity.
  - Upon login, the user is greeted either with a welcome, or a search bar, depending whether or not they have any existing ratings.
  - Upon logout, the user is returned to the initial landing screen, full of generic recommendations.

- Search bar
  - A user can search a dataset containing over 270,000 books and almost 100,000 authors, by book title, author name, or ISBN.
  - Protects against malformed input.
  - Results are then displayed in a carousel; books that the user has already read are not filtered.
  - The user can simply a corner exit button to reset the search.
  
- 'My Ratings' list
  - Users can track what they've already read and view it on the carousel by clicking the 'My Ratings' button on the nav-bar.
  - All previous ratings given are shown.
  
- 'My Recommendations' list
  - Comprised of two components: what similar users are reading, and recommended authors.
  - What similar users are reading is a list of books that the system deems as highly likely to be of interest, regardless of author.
  - A list authors is also recommended, and a list of the most highly scored books for each author is present to the user.

<b> Visual Demonstration </b>
-
Note: The dataset used here is fairly old, and does not seem to contain any books published past 2005.
