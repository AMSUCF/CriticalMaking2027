---
title: "Making Exercise Eight: Analysis"
canvas:
  module: "Week Nine: Analysis"
  week_start: 2027-03-08
  due: 2027-03-14
  close: 2027-03-28
  points: 7
  discussion: true
  discussion_title: "Making Exercise Eight: Analysis"
  rubric: true
  interview: daedal
---
# Making Exercise Eight: Analysis

## Think: Analysis

This week, we'll be working with Voyant and thinking more broadly about values and visualization: how our understanding of language and culture intersects with our understanding of AI, and how every act of counting, sorting, and charting is also an act of interpretation. Catherine D'Ignazio and Lauren Klein's feminist approach to data visualization asks us to make the choices behind a chart visible, while *Design Justice* asks who benefits from (and who is harmed by) the systems we design. Large language models are, in a sense, text analysis at an enormous scale: working with Voyant on a corpus you can actually hold in your head is a way of seeing what "distant reading" reveals, and what it flattens.

This week's featured interview with Quinn Daedal, a scholar, textile artist, and librarian, is available in Webcourses. As you embark on your own analysis, explore the examples linked in this week's readings, and think about how you might visualize your data in a way you find compelling.

## The Analysis Prompt

For this exercise you'll be performing an analysis of text with [Voyant](https://voyant-tools.org/), a web-based digital humanities tool that can work with a wide range of textual data sources directly. After you've found something interesting in the analysis, take your findings into an alternative visualization using any making method that feels appropriate to you -- GIF, comic, illustration, textile, Twine, etc. As you work with Voyant and visualize the results, keep in mind:

- **Explore the possibilities of Voyant itself.** Try the different built-in tools for visualization and textual exploration detailed below and think about this linkage, and particularly how the act of making text visual is in dialogue with our larger conversations around image-text as well as other tools for visualization we’ve considered.

- **Explore meaning at scale.** Working with a small set of texts won’t really allow you to see compelling patterns easily: this type of exploration works best with very large datasets. Look at examples that build across novels, like the compelling work of the [Data-Sitters Club](https://datasittersclub.github.io/site/dsc6.html) visualizing all the *Baby-Sitters Club* books across the years.

- **Think about visualization as interpretation.** You can work in any materiality or format that makes sense for the visualization, from textile to comic and beyond. Document your visualization through photos, screenshots, or sharing the interactive work as appropriate to the form. It's ok for this visualization to be rough or to use speculative data at this stage.

As with our other exercises, make sure to include both a link to any digital elements as well as documentation of the process and your results from Voyant. For the experimental or material visualization, this might include sketches or iterations of your design.

## Getting Started with Voyant

1. **Choose a corpus.** Pick a set of texts connected to your research or interests: novels from [Project Gutenberg](https://www.gutenberg.org/ebooks/), a run of speeches, a collection of reviews, your own writing. More text gives you more to see. To practice first, use the **Open** option on Voyant's home page to load one of its sample corpora, such as Shakespeare's plays.
2. **Load it.** Go to [voyant-tools.org](https://voyant-tools.org/) and paste one or more URLs (one per line) or a block of text into the box, or select **Upload** to add files from your computer. Then select **Reveal**.
3. **Explore the default panels** described below, and follow anything surprising: click on words, swap panels, and edit the stopwords.
4. **Save your view.** Each panel has an export option (look for the arrow icon in its header) that lets you get a link to your corpus, an image of a visualization, or the underlying data. Grab screenshots as you go for your process documentation.
5. **Make it your own.** Take one compelling finding into your own visualization, as described at the end of this page.

If you'd like a guided tour, the [Voyant basics tutorial](https://www.youtube.com/watch?v=LWyMU0fWX58) and the [Voyant help guide](https://voyant-tools.org/docs/#!/guide/gallery) both walk through the interface.

## Visualizing Text

Voyant offers an ease of use in the browser that makes it fast to get started. Once you’ve loaded the tool itself, there are many options to bring in texts to analyze, including pasting the URL of the text to be analyzed or uploading it. Voyant produces word clouds, word frequencies, and more simple visualizations without the need to download any additional software, with the exceptions for websites that aren’t formatted initially in a way that Voyant can “read," which might be better scraped first.

After you upload a corpus to analyze, Voyant displays five panels of information. You will now see a top row consisting of three images: a word cloud under “Cirrus,” a list of phrases under “Reader,” and a chart of relative frequencies under “Trends.” Beneath this, are two additional informational panels: “Summary” which displays the total number of documents, words, and unique word forms in the corpus as well as other length and term metrics; and “Contexts” which displays a column of the most frequent terms (for the Shakespeare corpora, the term displayed initially is “shall”) and three to five words that appear before and after that word within the texts.

![Voyant](../img/voyant.jpg)

From this starting point, you can further investigate your corpus by selecting other options in the tool. In the word cloud under “Cirrus,” Voyant automatically applies a list of stopwords, or words to exclude from the word cloud. These can be edited by hovering over the blue question mark next to “Links,” and clicking the blue slider symbol. This brings up editing options for the stopwords (words to exclude), white list (words to never exclude), categories, font family, and palette. Clicking “edit list” beside any of these, the user can add or remove from the list. Color palette and font options are of course more limited. The use of stopwords and the ability to edit the list is immensely useful; the researcher can remove obvious key words for a closer inspection of less obvious frequently used words. The way that Voyant seamlessly integrates the editing is also much more user-friendly than some other text analysis tools like Orange, which require the user to upload the entire document of stopwords.

Beside “Cirrus,” you can select “Terms” and see the exact number of times each word appears in a corpus. For the pre-loaded Shakespeare corpus, “shall” appears 3,594 times. Beside “Terms,” clicking “Links” displays a network graph of words that appear near these high-frequency words. Hovering the mouse over the blue key words will show their total frequency in the corpus, but hovering over the orange collocated words shows the number of times they appear near the blue key word, and not the total number of times they appear in the corpus. In the Shakespeare corpus, “shall” is used 3,594 times, and near shall, “come” appears 129 times, “know” 100 times, “make” 107 times, and “sir” 107 times.

Beside “Reader” in the next column, the user can select “TermsBerry.” Aptly named, this panel displays high frequency terms in berry-like circles. Hovering over one of the terms highlights that term in green, and highlights other related terms in dark or light red. Selecting “distinct terms” under the drop-down “Strategy” in this panel brings circles of names. Hovering over “Capulet” in the Shakespeare corpus highlights that surname in green, and “Romeo” and “Juliet” in light red.

The “Trends” graph displays the most frequent words in the corpus across its distinct documents, but clicking on a term in the “TermsBerry” panel beside it displays just that term. In the bottom row, beside “Summary,” the user can select “Documents” where metrics for each document are displayed; or “Phrases” which shows multi-word phrases that appear more than once in a document. Phrases can be sorted by frequency or word length of phrases, and in the box beneath the “Contexts” panel, any term can be entered to display the contexts; clicking “Correlations” in that panel allows for text to be entered in the same box to view word correlations. Clicking on the button “scale” at the very bottom of the “Contexts” or “Correlations” panel (after clicking the > button to scroll the bottom menu) allows phrases to be searched by corpus or document.

Once you've used these methods to find something interesting, take just that data to your own visualization: this can be material or digital, but should draw out something compelling from the data that wouldn't otherwise be easy to "see." If you'd like, you can also bring your exported data to Claude to prototype a digital version, as you did with the map in Week Five; if you do, make the interpretive choices yourself, and notice which choices the AI tries to make for you.

### Discussion

Share your completed analysis and visualization, following the pattern above. Your post should include:

- **Process documentation (3 points):** approximately five images or screenshots from both your use of Voyant and your alternative data visualization, with a short narrative that walks through your thinking.
- **Engagement with the readings (2 points):** connections to the readings and examples, including citations of at least two works from this module.
- **Peer responses (2 points):** at least two thoughtful replies to your peers' work.

Each week's discussion stays open for no-penalty late submissions and further conversation for at least one week after the deadline; because spring break follows, this one stays open through the break and the week after it. After that, it closes for both submissions and replies.
