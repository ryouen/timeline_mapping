const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({
    viewport: { width: 375, height: 667 } // iPhone SEのサイズをシミュレート
  });

  try {
    console.log('Navigating to https://japandatascience.com/timeline-mapping/');
    await page.goto('https://japandatascience.com/timeline-mapping/');
    await page.waitForLoadState('networkidle');
    console.log('Page loaded.');

    // スクリーンショットを撮る (初期状態)
    await page.screenshot({ path: 'initial_state.png' });
    console.log('Initial state screenshot saved to initial_state.png');

    // ボトムシートのハンドル要素を探す
    const bottomSheetHandle = await page.$('.sheet-handle');
    if (bottomSheetHandle) {
      console.log('Found .sheet-handle. Clicking it...');
      await bottomSheetHandle.click();
      await page.waitForTimeout(1000); // 1秒待機してアニメーションを待つ
      await page.screenshot({ path: 'after_click_handle.png' });
      console.log('After click handle screenshot saved to after_click_handle.png');

      // もう一度クリックして元に戻す
      await bottomSheetHandle.click();
      await page.waitForTimeout(1000); // 1秒待機してアニメーションを待つ
      await page.screenshot({ path: 'after_second_click_handle.png' });
      console.log('After second click handle screenshot saved to after_second_click_handle.png');
    } else {
      console.log('.sheet-handle not found.');
    }

    // 物件チップの数を検証
    const propertyChips = await page.$$('.property-chip');
    console.log(`Number of property chips: ${propertyChips.length}`);

    // 物件情報エリアの見出しを検証
    const areaInfoHeading = await page.$('div.area-info h3');
    if (areaInfoHeading) {
      const headingText = await areaInfoHeading.textContent();
      console.log(`Area info heading text: "${headingText.trim()}"`);
    } else {
      console.log('Area info heading (h3) not found.');
    }

  } catch (error) {
    console.error('An error occurred:', error);
  } finally {
    await browser.close();
  }
})();