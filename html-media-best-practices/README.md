# HTML Media Best Practices README

## Index

1. [One image](one-image.html)
2. [Three images](three-images.html)
3. [Three images lazy loaded](three-images-lazy-loaded.html)
4. [One video](video-test-1a.html)
7. [One video](video-test-1a_no-poster.html) (no poster image)
8. [One video](video-test-1a_no-poster_mp4-only.html) (no poster. no webm; mp4 only)
7. Three videos
8. Three videos lazy loaded
4. [Embedded Video: YouTube](youtube-embed-testing.html)
5. [Embedded Video: Vimeo](vimeo-embed-testing.html)

## Notes

Videos and moving images should:

1. be captioned (unless there is no audio).
2. if five seconds or longer, should have pause, stop or hide controls
3. be keyboard operable

## References

### Accessibility

WCAG 2.1 was published on June 5, 2018.  WCAG 2.2 Draft is scheduled to be finalized in 2023.

#### WCAG 2.2

- [Success Criterion 1.2.2 Captions (Prerecorded)](https://www.w3.org/TR/WCAG22/#captions-prerecorded): Captions are provided for all prerecorded audio content in synchronized media, except when the media is a media alternative for text and is clearly labeled as such. 
- [Success Criterion 1.4.2 Audio Control](https://www.w3.org/TR/WCAG22/#audio-control): If any audio on a Web page plays automatically for more than 3 seconds, either a mechanism is available to pause or stop the audio, or a mechanism is available to control audio volume independently from the overall system volume level. 
- [Success Criterion 2.1.1 Keyboard](https://www.w3.org/TR/WCAG22/#keyboard): All functionality of the content is operable through a keyboard interface without requiring specific timings for individual keystrokes, except where the underlying function requires input that depends on the path of the user's movement and not just the endpoints. 
- [Success Criterion 2.2.2 Pause, Stop, Hide](https://www.w3.org/TR/WCAG22/#pause-stop-hide): For moving, blinking, scrolling, or auto-updating information, all of the following are true:

    Moving, blinking, scrolling

        For any moving, blinking or scrolling information that (1) starts automatically, (2) lasts more than five seconds, and (3) is presented in parallel with other content, there is a mechanism for the user to pause, stop, or hide it unless the movement, blinking, or scrolling is part of an activity where it is essential; and

    Auto-updating

        For any auto-updating information that (1) starts automatically and (2) is presented in parallel with other content, there is a mechanism for the user to pause, stop, or hide it or to control the frequency of the update unless the auto-updating is part of an activity where it is essential.

    - WCAG 2.2: [Understanding SC 2.2.2](https://www.w3.org/WAI/WCAG22/Understanding/pause-stop-hide)

- [Success Criterion 2.3.1 Three Flashes or Below Threshold](https://www.w3.org/TR/WCAG22/#three-flashes-or-below-threshold): Web pages do not contain anything that flashes more than three times in any one second period, or the flash is below the general flash and red flash thresholds.

#### Captions

<ul>
    <li>mdn web docs: <a href="https://developer.mozilla.org/en-US/docs/Web/Guide/Audio_and_video_delivery/Adding_captions_and_subtitles_to_HTML5_video">Adding captions and subtitles to HTML video</a></li>
    <li>mdn web docs: <a href="https://developer.mozilla.org/en-US/docs/Web/HTML/Element/track">The Embed Text Track element</a></li>
    <li>mdn web docs: <a href="https://developer.mozilla.org/en-US/docs/Web/API/WebVTT_API">Web Video Text Tracks Format (WebVTT)</a></li>
    <li>W3C Web Accessibility Initiative: <a href="https://www.w3.org/WAI/media/av/captions/#captions-and-subtitles">Captions/Subtitles</a></li>
    <li>W3C: <a href="https://www.w3.org/wiki/VTT_Concepts">VTT Concepts</a></li>
</ul>

### Animation

- [Accessible Web Animation: The WCAG on Animation Explained](https://css-tricks.com/accessible-web-animation-the-wcag-on-animation-explained/)
    - WCAG: [Pause, Stop, Hide (Level A)](https://www.w3.org/WAI/WCAG21/Understanding/pause-stop-hide.html)
- MDN Web Docs: [Accessible multimedia](https://developer.mozilla.org/en-US/docs/Learn/Accessibility/Multimedia)

### Images

#### GIFs

- [Pausing a GIF with details/summary](https://css-tricks.com/pause-gif-details-summary/)

### Video

- [Making Audio and Video Media Accessible ](https://www.w3.org/WAI/media/av/)
- UCSF: [Accessible Videos Best Practices](https://it.ucsf.edu/how-to/accessible-videos-best-practices)

#### Background Video

- [Accessible HTML video as a background](http://www.punkchip.com/accessible-html-video-as-a-background/)

Example of what not to do: https://www.tesla.com/modely

Example of what to do:

### Lazy-Loading

- MDN Docs: [Lazy Loading](https://developer.mozilla.org/en-US/docs/Web/Performance/Lazy_loading)

#### Images

- [Browser-level image lazy loading for the web](https://web.dev/browser-level-image-lazy-loading/)
- Drupal: [lazy-load](https://www.drupal.org/project/lazy)

#### Video

- [Lazy loading video](https://web.dev/lazy-loading-video/)

##### Background Video

- [Best Practices for HTML Background Video Optimization](https://www.gomasuga.com/blog/best-practices-for-html-background-videos)

### Responsive CSS Grid

- [A responsive grid layout with no media queries](https://css-tricks.com/a-responsive-grid-layout-with-no-media-queries/)
- [Realizing common layouts using grids](https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_grid_layout/Realizing_common_layouts_using_grids)
- Codepen: [Responsive CSS Grid Layout](https://codepen.io/SitePoint/pen/NWOGvvN?editors=1100)
- Codepen: Andy Bell's [Responsive Grid Layout](https://codepen.io/andy-set-studio/pen/vMMYKJ)

### Benchmarking

- https://www.webpagetest.org/ 

## Thanks & Credits

- 512 x 288 GIF by <a href="https://pixabay.com/users/nickype-10327513/?utm_source=link-attribution&utm_medium=referral&utm_campaign=animation&utm_content=1782">Nicky ❤️🌿🐞🌿❤️</a> from <a href="https://pixabay.com//?utm_source=link-attribution&utm_medium=referral&utm_campaign=animation&utm_content=1782">Pixabay</a>

- Thank you cloud convert: https://cloudconvert.com/mov-to-webm