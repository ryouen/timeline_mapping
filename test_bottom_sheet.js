const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext({
    isMobile: true,
    viewport: { width: 375, height: 667 }, // iPhone SE dimensions
    hasTouch: true // Enable touch support
  });
  const page = await context.newPage();

  try {
    await page.goto('https://japandatascience.com/timeline-mapping/');

    // --- Test for main bottom sheet --- //
    const bottomSheet = page.locator('#bottomSheet');
    await bottomSheet.waitFor({ state: 'visible' });

    // Initial state: collapsed (check absence of 'expanded' and 'active' class)
    let isExpandedInitially = await bottomSheet.evaluate(el => el.classList.contains('expanded'));
    let isActiveInitially = await bottomSheet.evaluate(el => el.classList.contains('active'));
    if (isExpandedInitially || isActiveInitially) {
      throw new Error('Main bottom sheet is expanded or active initially, but should be collapsed.');
    }
    console.log('Main bottom sheet is initially collapsed.');

    // Tap the handle to expand
    const sheetHandle = page.locator('.sheet-handle');
    await sheetHandle.tap();
    console.log('Tapped sheet handle to expand main bottom sheet.');

    // Wait for the expanded state
    await bottomSheet.waitFor(async el => el.classList.contains('expanded') && el.classList.contains('active'), { timeout: 5000 });
    isExpandedInitially = await bottomSheet.evaluate(el => el.classList.contains('expanded'));
    isActiveInitially = await bottomSheet.evaluate(el => el.classList.contains('active'));
    if (!isExpandedInitially || !isActiveInitially) {
      throw new Error('Main bottom sheet did not expand or activate after first tap.');
    }
    console.log('Main bottom sheet expanded successfully after first tap.');

    // Tap the handle again to collapse
    await sheetHandle.tap();
    console.log('Tapped sheet handle to collapse main bottom sheet.');

    // Wait for the collapsed state
    await bottomSheet.waitFor(async el => !el.classList.contains('expanded') && !el.classList.contains('active'), { timeout: 5000 });
    isExpandedInitially = await bottomSheet.evaluate(el => el.classList.contains('expanded'));
    isActiveInitially = await bottomSheet.evaluate(el => el.classList.contains('active'));
    if (isExpandedInitially || isActiveInitially) {
      throw new Error('Main bottom sheet did not collapse after second tap.');
    }
    console.log('Main bottom sheet collapsed successfully after second tap.');

    // --- Test for sort bottom sheet --- //
    const sortBottomSheet = page.locator('#sortBottomSheet');
    const openSortSheetBtn = page.locator('#openSortSheetBtn');
    const sortSheetCloseBtn = page.locator('#sortBottomSheet .close-btn');
    const applySortBtn = page.locator('.apply-sort-btn');

    // Initial state: sort bottom sheet should be hidden
    let isSortSheetActive = await sortBottomSheet.evaluate(el => el.classList.contains('active'));
    let isSortSheetVisible = await sortBottomSheet.isVisible();
    if (isSortSheetActive || isSortSheetVisible) {
      throw new Error('Sort bottom sheet is active or visible initially, but should be hidden.');
    }
    console.log('Sort bottom sheet is initially hidden.');

    // Open sort bottom sheet
    await openSortSheetBtn.tap();
    console.log('Tapped open sort sheet button.');

    // Wait for sort bottom sheet to be active and visible
    await sortBottomSheet.waitFor({ state: 'visible' });
    isSortSheetActive = await sortBottomSheet.evaluate(el => el.classList.contains('active'));
    if (!isSortSheetActive) {
      throw new Error('Sort bottom sheet did not become active after tap.');
    }
    console.log('Sort bottom sheet is active and visible.');

    // Close sort bottom sheet using close button
    await sortSheetCloseBtn.tap();
    console.log('Tapped sort sheet close button.');

    // Wait for sort bottom sheet to be hidden
    await sortBottomSheet.waitFor({ state: 'hidden' });
    isSortSheetActive = await sortBottomSheet.evaluate(el => el.classList.contains('active'));
    if (isSortSheetActive) {
      throw new Error('Sort bottom sheet is still active after closing.');
    }
    console.log('Sort bottom sheet is hidden after closing with close button.');

    // Re-open sort bottom sheet to test apply button
    await openSortSheetBtn.tap();
    await sortBottomSheet.waitFor({ state: 'visible' });
    console.log('Re-opened sort bottom sheet for apply button test.');

    // Apply sort order
    await applySortBtn.tap();
    console.log('Tapped apply sort button.');

    // Wait for sort bottom sheet to be hidden after apply
    await sortBottomSheet.waitFor({ state: 'hidden' });
    isSortSheetActive = await sortBottomSheet.evaluate(el => el.classList.contains('active'));
    if (isSortSheetActive) {
      throw new Error('Sort bottom sheet is still active after applying sort.');
    }
    console.log('Sort bottom sheet is hidden after applying sort.');

    console.log('All tests passed: Both bottom sheets function correctly.');

  } catch (error) {
    console.error('Test failed:', error);
    process.exit(1);
  } finally {
    await browser.close();
  }
})();
