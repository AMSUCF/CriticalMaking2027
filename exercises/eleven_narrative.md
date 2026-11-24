---
title: "Making Exercise Eleven: Narrative"
canvas:
  module: "Week Thirteen: Narratives"
  week_start: 2027-04-05
  due: 2027-04-11
  close: 2027-05-02
  points: 7
  discussion: true
  discussion_title: "Making Exercise Eleven: Narrative"
  rubric: true
  interview: bessette
---
# Making Exercise Eleven: Narrative

## Think: Narrative

This week we'll be continuing to experiment with P5.js and thinking about the act of learning to code, and how that act is changing in light of the widespread availability of agentic AI tools. If an agent can write the code, what is left for us to learn, and what do we risk losing if we stop learning it? For a thoughtful outside perspective, I recommend [this talk from Simon Willison](https://www.youtube.com/watch?v=wc8FBhQtdsA), one of the people whose insights I most trust when looking at the impact of AI on code and computational labor (the first 40 minutes are the most relevant to us). The Data-Sitters Club's reflections on [learning to code](https://datasittersclub.github.io/site/dsc12.html) and on [agentic AI coding](https://datasittersclub.github.io/site/dsc23.html) make a great pair as you think about your own learning.

This week's featured interview with Lee Skallerup Bessette is available in Webcourses. Her [*Adjunct Run*](https://adjunctrun.readywriting.org/) and [*Word Vomit*](https://readywriting.github.io/wordvomit/) are both small, personal, playful works that make an argument through interaction.

As we continue our play with P5.js, conceptualize a project that uses P5.js for a more significant playful, narrative, or interactive purpose. You might draw on influences such as [*Algorithmic Sea*](https://www.algorithmicsea.com/) and [*Strange Rain*](https://erikloyer.com/index.php/projects/detail/strange_rain), shown below, or you can build on a concept you started last week or earlier in the semester.

![Strange Rain](../img/rain.png)

Think of this as a free-form exercise to take your work with agentic tools to a next level: try sharing a prototype, design notes, data, and anything else that is relevant to your goals in the GitHub repository before you start. Make sure to ask the agent to plan first, so you can think through the idea and clarify the design before it starts implementation.

## The Narrative Prompt

As we'll be taking our inspiration from electronic poetry and narratives as a form of making this week, this is a free-form exercise in building your P5.js knowledge while exploring computational creativity. Work between existing code and agentic tools: I recommend building a prototype or outline first, moving it into GitHub, and then expanding it with agentic tools, following the workflow below. I've provided three starters that suggest different possibilities for working with P5.js to allow for moving or interactive text, but feel free to try something different as a starting point. Explore their capabilities first, and then think about making your own. There are suggestions in each for ways to push the style, text, and design further. Focus on:

- **Experiment with code and debugging.** Try things, and break it. Modify small aspects of the code directly in GitHub (see step 5 below). Consider loading in images (add them to your GitHub repository), exploring interactivity, and think about how you can work from basic shapes and text to leave an impression. Remember, if you break things you can always go back and fork the original code.

- **Change aesthetics and poetics.** Play with the text, and think about how you can use text and color to convey emotion. Try building a mood, and consider branching out to draw in images or create a sense of space.

- **Generate your own elements.** Using [Claude Code](https://claude.ai/code) on the web and building on our efforts in the last two exercises, extend your project in a direction you find compelling. Think about the examples provided, and try to use precise prompting and edit the resulting code/text as needed to achieve your goals.

As always, include links and screenshots of your forked experiments and the new prototype on GitHub.

## Walkthrough and Resources

For an extended example of this way of working, check out my piece in _Kairos,_ ["AI Admin: Provocations through Generated Play."](https://kairos.technorhetoric.net/30.2/disputatio/salter/) The first version was built in 2024, before agentic tools were particularly capable, and thus includes a lot of hand-written code and my own work. The second version was built with the agentic workflow described below, using the first as a prototype to iterate and expand upon.

If you want a simple starter to manipulate, consider using one of these:

- [Click Poetry](https://openprocessing.org/sketch/1325975) builds on our last mouse interaction piece: click to place a line of text. The work will cycle through a text in order, allowing for a sense of narrative progression or poetry if you write your lines intentionally. The text gradually fades from the screen.
- [Falling Text](https://openprocessing.org/sketch/1325914) uses a simple particle system to create moving text, inspired by *Strange Rain.* Don't worry about changing the code for the particle system itself: you can manipulate the speeds, positions, colors, and text to transform the experience.
- [Moving Click Text](https://openprocessing.org/sketch/1325979) combines elements of the other two examples to create moving text where the user clicks. The lines will become unreadable as they shift across the screen and fade. Again, don't worry about changing the code for the particle system itself.

### From prototype to agentic project, step by step

1. **Prototype by hand.** Fork one of the starters on OpenProcessing (or start from your sketch last week) and make your first changes there: your own text, colors, and pacing. This is your prototype.
2. **Make a repository.** Create a new public GitHub repository with a README, as in [Making Exercise Nine](nine_generation).
3. **Move your sketch into GitHub.** Select **Add file → Create new file**, name it `index.html`, and paste in this page, which loads the P5 library and then your sketch:

   ```html
   <!DOCTYPE html>
   <html>
     <head>
       <meta charset="utf-8">
       <title>My Narrative Sketch</title>
       <script src="https://cdn.jsdelivr.net/npm/p5@1.9.4/lib/p5.min.js"></script>
       <script src="sketch.js"></script>
     </head>
     <body></body>
   </html>
   ```

   Commit it, then create a second file named `sketch.js` and paste in all the code from your OpenProcessing sketch. (If your sketch uses any extra libraries, add a `<script>` line for each one, too.)
4. **Publish it.** Turn on GitHub Pages under **Settings → Pages** (deploy from the **main** branch, **/ (root)** folder), and check that your sketch runs at your new site address.
5. **Edit directly.** To make a small change by hand, open a file in your repository, select the pencil icon (**Edit this file**), make your change, and select **Commit changes**. Your site updates within a minute or two. This is a good way to tweak text and colors without involving an agent at all.
6. **Add your context.** Upload anything that will help the agent understand your goals: design notes, a sketch of the interface, images, the text you want to use. A short `notes.md` file describing your intention is a great start.
7. **Plan with the agent.** Open the repository in [Claude Code](https://claude.ai/code) and ask it to read your files and propose a plan *before* writing any code. Revise the plan until it matches your intention, then let it build.
8. **Review, test, and merge.** Read the changes, test the result, merge them into your main branch, and check the live site. Then keep going: debug directly and by asking the agent to fix glitches, one small step at a time.

I recommend breaking your goal (whether it's a game, narrative experiment, etc.) down into simple steps, and making sure you test everything at each step. If you want to explore further, try following the exercises in the [Creative Coding](https://creative-coding.decontextualize.com/) resources.

### Discussion

Share your narrative project, following the pattern above. Your post should include:

- **Process documentation (3 points):** approximately five images or screenshots from your conversation and the objects created as part of the process, including links to your forked experiments and your new prototype on GitHub, with a short narrative that walks through your thinking.
- **Engagement with the readings (2 points):** connections to the readings and examples, including citations of at least two works from this module.
- **Peer responses (2 points):** at least two thoughtful replies to your peers' work.

Each week's discussion stays open for no-penalty late submissions and further conversation for at least one week after the deadline; as we near the end of the semester, this one stays open through the course's final deadline. After that, it closes for both submissions and replies.
