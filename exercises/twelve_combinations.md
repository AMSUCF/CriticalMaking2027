---
title: "Making Exercise Twelve: Combinations"
canvas:
  module: "Week Fourteen: Combinations"
  week_start: 2027-04-12
  due: 2027-04-18
  close: 2027-05-02
  points: 7
  discussion: true
  discussion_title: "Making Exercise Twelve: Combinations"
  rubric: true
  interview: barnes
---
# Making Exercise Twelve: Combinations

## Think: Combinations

Now that we're nearing the end of the semester, we'll be reflecting on, collecting, and curating the work you've produced. This week's readings think about the book, the archive, and data beyond vision, and about what it means, in Natalie Loveless's terms, to make art (and scholarship) "at the end of the world." For a great example of critical making with a public audience in mind, look at Casey Fiesler's short [explainers on how large language models work](https://www.youtube.com/watch?v=VZB8XCcyllE), designed for TikTok: she combines her research expertise with the platform's vernacular to make something both rigorous and approachable.

This week's featured interview with Nikki Fragala Barnes, a Texts & Technology PhD graduate whose work braids critical making, communal pedagogies, museum practice, and experimental poetics, is available in Webcourses.

This week's exercise is focused on remixing, combining, and extending the work you've already done, integrating your own expertise and code with agentic tool assistance. You can use both hand-coded and agentic solutions to make those changes: this might include integrating P5 with Twine and/or Bitsy, building GIF-illustrated hypertexts, adding Tracery to your P5, and beyond. Going back to the basics (such as comics and hypertext) can also be a great way to bring together the components of your making, material and digital. Leave time for debugging these combinations, as even HTML and JavaScript files can be difficult to combine without errors.

<iframe src="https://openprocessing.org/sketch/2237599/embed/?plusEmbedHash=3f441452&userID=293182&show=sketch" width="600" height="600"></iframe>

My example combination project is available to explore live [on GitHub Pages](https://anastasiasalter.net/CombinationsCritMaking/), and can be referenced for code samples in [the repository](https://github.com/AMSUCF/CombinationsCritMaking). You can also fork the examples on OpenProcessing: [the linked escape room](https://openprocessing.org/sketch/2237599) and the [Tracery P5 integration](https://openprocessing.org/sketch/2237590). The escape room is also embedded above, which is an example of dropping an iframe into Markdown.

For a smaller example you can take apart, try the course's Twine remix, [*Critical Making: The Remix*](materials/ReRemix.html). It's a Twine story that displays an animated GIF and images, links out to a Bitsy game ([*Critical Making Remixed*](materials/critremix.html)) and to two P5 sketches (the [Tracery demo](materials/tracery.html) and the [RiTa demo](materials/rita.html)), and uses an iframe to embed a story map inside a passage. All of those files sit side by side in one folder, which is what makes the simple links below work.

Keep in mind the following simple methods for linking and combining materials before you get fancy with Claude Code:

- **iframes** - As shown above, iframes are an excellent way to combine two very different types of material: you can use an iframe to link to another HTML file in your repository and include it in a box inside any other page--for instance, you can display a P5.js sketch or a Bitsy game inside a Twine passage. Here's an example of proper iframe code - just change the html file name to the name of another file in your repository, and adjust the width and height as needed:

```
<iframe src="anotherfile.html" width="600" height="600"></iframe>
```

- **Adding images** - Adding your comic, GIF, selfie, or other image to a HTML file is a two step process. First, upload the image file to the repository where you'll be working: I recommend uploading everything you plan to use before you start. Adding an image to the Twine or as a header above your Bitsy game is fairly straightforward - you can use an image tag, as shown below. For P5.js, reference the code in the linked escape room example:

```
<img src="imagename.jpg">
```

- **Relative links** - If you've uploaded all your html files into the same directory, remember that whichever file you label as index.html will be the default that displays on your GitHub Pages site. If you don't designate one file as index.html, your GitHub Pages site will give a 404 error. Simple links are an easy way to progress from say a Bitsy to a Twine, P5 to a Bitsy game, etc, but you can also use Claude Code to create more complex links from the ending passages or conditions of your interactive pieces. Here's the basic link:

```
<a href="otherfile.html">Text of the link.</a>
```

## Putting It Together, Step by Step

1. **Gather your ingredients.** Download the .html files of your earlier work (your Twine from "Publish to File," your Bitsy download, your P5 code) and the images you want to use.
2. **Make one home for everything.** Create a new GitHub repository (as in [Making Exercise Nine](nine_generation)) and upload all of your files to the same folder. Rename the piece readers should see first to `index.html`.
3. **Connect by hand first.** Use the iframes, image tags, and links above to make at least one connection yourself: in Twine, you can paste HTML directly into a passage; for Bitsy, add a link or image above or below the game in the .html file.
4. **Bring in the agent.** Open the repository in [Claude Code](https://claude.ai/code), describe your theme and how the pieces should connect, and ask for a plan before any code is written. Good requests are specific: "When the reader reaches the ending passage of the Twine, link to the Bitsy game," or "use the same color palette and font across all three pieces."
5. **Publish and test.** Turn on GitHub Pages (**Settings → Pages**, deploy from **main**, **/ (root)**), then click through every path as a reader would. Fix broken links and missing images first: these are the most common problems, and they're usually a typo in a file name (names are case-sensitive!).

## The Multimodal Prompt

This week's prompt is intentionally flexible to allow you to choose the tools, platforms, and experiments from our previous weeks that you most want to revisit and expand upon. Here's a broad recipe for your multimodal making:

- **Combine at least three ingredients** - Depending on your interests, these might include more visual, procedural, or data-driven components that work well together. For example, Tracery combines well with P5.js, and both might make a fantastic "prelude" to a Twine piece geared towards *Kairos* or *the digital review.* Note the three tools you used and why you selected them in your introduction to your reflection prompt.

- **Convey a coherent theme.** - Approach your multimodal exercise as a coherent whole: rather than showcasing the technologies and making exercises from previous iterations as fragmented components, revisit each part and think about how it adds to an overall theme. Revisiting your text will help draw the pieces together. Agentic tools can help with making the works "fit" together technically, but you need to guide the intention of the pieces.

- **Work towards aesthetic unity.** - Think about ways to connect the components of your work visually: can you revisit font choices? Use a shared color palette? Try to avoid drawing attention to the separate pieces of your work - instead, play with strategies to bring the interfaces, and ideas, together.

As always, please share screenshots from your process as well as a link to your new piece on GitHub Pages.

### Discussion

Share your combined piece, following the pattern above. Begin your post by naming the three (or more) ingredients you combined and why you selected them. Your post should include:

- **Process documentation (3 points):** approximately five images or screenshots from your conversation and the objects created as part of the process, a link to your new piece on GitHub Pages, and a short narrative that walks through your thinking.
- **Engagement with the readings (2 points):** connections to the readings and examples, including citations of at least two works from this module.
- **Peer responses (2 points):** at least two thoughtful replies to your peers' work.

Each week's discussion stays open for no-penalty late submissions and further conversation for at least one week after the deadline; as we near the end of the semester, this one stays open through the course's final deadline. After that, it closes for both submissions and replies.
