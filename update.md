## Roadmap
1. Modify captcha to handle 4x4

Currently targets the image src based on `image_grid` CSS selector which is hard-coded to a 3x3 grid search. Should modify the selector to wait for a 3x3 or a 4x4. Then based on which one is waited for should pass 3, 4 as input to decaptcha to know how to `split_and_encode` image.

2. Run faster

Figure out how to use `processes`. Multi-threading?

3. Clean-up form filling flow

    - fill form
        - check for table [update `utils.get_faculty_department()` to quick-check for no results and update state]
            CSS selector `#Content > div > div:nth-child(3) > div > div > div`.
        - no table -> pass to captcha
        - check for table   
    - get & write dept
4. Clean-up repo
- Remove unused files