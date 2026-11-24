---
title: "Making Exercise Nine: Generation"
canvas:
  module: "Week Eleven: Generation"
  week_start: 2027-03-22
  due: 2027-03-28
  points: 7
  discussion: true
  discussion_title: "Making Exercise Nine: Generation"
  rubric: true
  interview: flores
---
# Making Exercise Nine: Generation

## Think: Generation

As we continue to move between procedural and interface-driven tools, we'll be exploring the disruptions promised by the increased accessibility of agentic AI tools as a means of "making." This semester, we've been focused on "slow" making and intentional use of digital tools for human expression and scholarly communication. Can agents, which take over a great deal of computational workflow, be a part of that process? This week's readings offer some lenses: Ethan Mollick on the uneven, "jagged" shape of AI capability, Kate Crawford and Trevor Paglen on the politics embedded in training data, and *Design Justice* on the values built into every design process.

This week's featured interview with Leonardo Flores is available in Webcourses. His [website](https://leonardoflores.net/), built with Claude Code, is itself an example of the kind of making we're trying this week.

AI-assisted code generation offers great potential for meaningful critical making projects—especially when approached as a conversation between human intent and machine output. The work of generation is collaborative and iterative: you guide the process through prompting, evaluating, and refining, while the AI assists with code, structure, and design. Quirks and emergence can contribute to the overall work, and we embrace these much like Marshall McLuhan’s famous cover typo of “massage” instead of “message.” Whatever you choose to make, start with your own content and intention, and keep both at the center as you experiment. As you engage in generation, consider:

- **Probe the conversational limitations.** Try starting vague, or working with different ways of phrasing and expressing ideas to see where meaning is conveyed and where it is lost. These conversations are in part an opportunity to see what is included in the underlying archives (training data)—can you tell what might be missing?
- **Explore a range of expressive outputs.** Machine learning models are particularly powerful for assistance in programming and development work, as tools like GitHub Copilot suggest: in time, it’s likely these tools will be an inescapable part of certain workflows. Think about where the AI assists your making, and where it is limiting.
- **Contextualize the experience.** How does the system you are co-creating with reflect the headlines, fears, and assumptions that both generations of science fiction writers and current journalists have centered in their visions of AI futures?

## Getting Started

If you're looking for inspiration, here are three project types you can use as a starting point. Each is modeled on the workshop exercises at [Distant Coding with Claude Code](https://anastasiasalter.net/DistantCodingUMKC/), where you can see sample outputs and detailed walkthroughs. You are not limited to these—feel free to adapt them or pursue a different generative project entirely.

### Option A: Building an ePortfolio from a CV

Upload your CV (as a Word document or PDF) to a GitHub repository and use Claude Code to transform it into a single-page portfolio website. Through conversation, guide the AI to analyze your document, design an appropriate aesthetic, and build a site with sections for your publications, presentations, teaching, projects, awards, and education. Deploy the result via GitHub Pages. (Remove anything you don't want public, such as your phone number or home address, before you upload: anything in a public repository can be seen by anyone.)

### Option B: Distant Reading a Text Corpus

Select three to five plain-text files from [Project Gutenberg](https://www.gutenberg.org/) related to a theme or research interest. Use Claude Code to preprocess the texts (stripping formatting, tokenizing, removing stopwords, computing word frequencies), identify shared key terms, and extract keyword-in-context concordances. Then have Claude build an interactive web visualization displaying word distributions, frequency comparisons, and searchable concordance data, deployed via GitHub Pages. This is a nice chance to compare the experience with your work in Voyant in Week Nine.

### Option C: Image Metadata and Slideshow from Photographs

Gather a set of your own photographs (or public domain images) around a theme. Use Claude Code to analyze each image, generate descriptive alt-text for accessibility, and rename files meaningfully. Then guide Claude to construct a themed slideshow using reveal.js with custom styling and captions, deployed via GitHub Pages.

## How to Work

For AI-assisted coding in this course, I recommend using [Claude Code](https://claude.ai/code) in your browser, which provides an integrated environment for conversational code generation and debugging without requiring local installation. Claude Code can access and modify a GitHub repository, generate your project files, and help you publish them on GitHub Pages—all through conversation. Here's the workflow, step by step:

1. **Set up a repository.** Create a free [GitHub](https://github.com/) account if you don't have one. Select **New repository**, give it a short name (this becomes part of your site's address), make it **Public**, and check the box to add a README.
2. **Add your materials.** In the repository, select **Add file → Upload files**, drag in your starting materials (your CV, your texts, your images), and select **Commit changes**.
3. **Connect Claude Code.** Open [Claude Code](https://claude.ai/code), connect your GitHub account when prompted, and select your new repository.
4. **Plan before building.** Describe your project, your audience, and the feeling you want the site to have, and ask Claude to propose a plan *before* writing any code (for example: "Before you write anything, look at the files in this repository and propose a plan for the site. Wait for my approval."). Read the plan carefully and push back on anything that doesn't match your intention: this is where your expertise matters most.
5. **Let it build, and pay attention.** As Claude works, it will narrate the steps it's taking and the files it's creating. Take screenshots of the plan, the conversation, and moments that surprise you: these are your process documentation.
6. **Bring the work into your main branch.** Claude Code saves its work to a new branch in your repository. When you're happy with it, create a pull request and merge it into your **main** branch (Claude Code offers a button for this, or you can do it from the **Pull requests** tab on GitHub).
7. **Publish with GitHub Pages.** In your repository, go to **Settings → Pages**. Under "Build and deployment," set the source to **Deploy from a branch**, choose **main** and **/ (root)**, and select **Save**. After a minute or two, your site will be live at `https://your-username.github.io/your-repository-name/`. GitHub Pages shows the file named `index.html` as your home page, so make sure your project has one.
8. **Iterate.** Visit the live site, note what isn't working, and return to Claude with specific feedback ("the publication list is in the wrong order," "the alt-text for image three misreads the scene"). Each time you merge new changes, the site updates automatically.

**If you'd rather not use Claude Code**, you can still complete any of these projects by working indirectly: use a free AI assistant (such as [claude.ai](https://claude.ai)'s free tier or another tool) to generate HTML, CSS, and JavaScript files through conversation, save them to your computer, then upload them to a GitHub repository yourself (steps 1, 2, and 7 above). The process is slower, but you'll see every file the AI produces, which can be a valuable way to learn how the pieces fit together.

## Reflection

Whichever project you choose, document your process and reflect critically on the experience. Keep in mind the readings in both *Design Justice* and *Your Computer is On Fire*, and make specific connections to the problems raised by these tools using those lenses. In your reflection, address:

- Which aspects of your project benefited from AI assistance? Which were impeded by it?
- What did the conversation reveal about the AI’s assumptions, gaps, or biases?
- How does the experience of co-creating with an AI connect to broader questions about labor, authorship, and justice in digital making?

### Discussion

Share your generated project and reflection, following the pattern above. Your post should include:

- **Process documentation (3 points):** approximately five images or screenshots from your conversation and the objects created as part of the process, a link to your project (your GitHub Pages site or repository), and a short narrative that walks through your thinking and responds to the reflection questions above.
- **Engagement with the readings (2 points):** connections to the readings and examples, including citations of at least two works from this module.
- **Peer responses (2 points):** at least two thoughtful replies to your peers' work.

Remember, each week's discussion stays open for no-penalty late submissions and further conversation for one week after the deadline. After that, it closes for both submissions and replies.
