#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

// Read the figma data
const figmaDataPath = './output/myproject/sections/portfolio-home/desktop/figma-data.json';
const figmaData = JSON.parse(fs.readFileSync(figmaDataPath, 'utf8'));

// Extract pricing data
const priceList = figmaData.children.find(child => child.name === 'Price list');
const cards = priceList.children;

console.log('='.repeat(80));
console.log('PRICING CARDS SPACING CALCULATION ALGORITHM');
console.log('='.repeat(80));
console.log();

// Calculate spacing for each card
cards.forEach((card, index) => {
    const cardNames = ['Free', 'Personal', 'Organization'];
    const cardName = cardNames[index];

    console.log(`CARD ${index + 1}: ${cardName.toUpperCase()}`);
    console.log('-'.repeat(50));

    console.log(`Card Container:`)
    console.log(`  Position: x=${card.x}, y=${card.y}`);
    console.log(`  Size: ${card.width} × ${card.height}px`);
    console.log();

    // Get child elements
    const textBlock = card.children.find(child => child.name.includes('Text-block'));
    const bulletPoint = card.children.find(child => child.name === 'Bullet-point');
    const button = card.children.find(child => child.name.includes('Btn'));

    // PADDING CALCULATIONS
    console.log(`1. CARD PADDING ANALYSIS:`);
    console.log(`   Mathematical Calculations:`);

    // Padding calculations based on first child (text-block) position
    const paddingTop = textBlock.y;
    const paddingLeft = textBlock.x;
    const paddingRight = card.width - (textBlock.x + textBlock.width);

    // Bottom padding based on button position
    const paddingBottom = card.height - (button.y + button.height);

    console.log(`   paddingTop = textBlock.y = ${textBlock.y}px`);
    console.log(`   paddingLeft = textBlock.x = ${textBlock.x}px`);
    console.log(`   paddingRight = cardWidth - (textBlock.x + textBlock.width)`);
    console.log(`                = ${card.width} - (${textBlock.x} + ${textBlock.width}) = ${paddingRight}px`);
    console.log(`   paddingBottom = cardHeight - (button.y + button.height)`);
    console.log(`                 = ${card.height} - (${button.y} + ${button.height}) = ${paddingBottom}px`);
    console.log();

    // INTER-ELEMENT MARGINS
    console.log(`2. INTER-ELEMENT MARGINS:`);
    console.log(`   Mathematical Calculations:`);

    // Margin between text-block and bullet-point
    const marginTextToBullet = bulletPoint.y - (textBlock.y + textBlock.height);
    console.log(`   Text-block to Bullet-point margin:`);
    console.log(`     = bulletPoint.y - (textBlock.y + textBlock.height)`);
    console.log(`     = ${bulletPoint.y} - (${textBlock.y} + ${textBlock.height}) = ${marginTextToBullet}px`);

    // Margin between bullet-point and button
    const marginBulletToButton = button.y - (bulletPoint.y + bulletPoint.height);
    console.log(`   Bullet-point to Button margin:`);
    console.log(`     = button.y - (bulletPoint.y + bulletPoint.height)`);
    console.log(`     = ${button.y} - (${bulletPoint.y} + ${bulletPoint.height}) = ${marginBulletToButton}px`);
    console.log();

    // BULLET POINT ANALYSIS
    console.log(`3. BULLET POINT SPACING:`);
    console.log(`   Container: ${bulletPoint.width} × ${bulletPoint.height}px`);
    console.log(`   Mathematical Calculations:`);

    // Get bullet point children from figma data
    let bulletChildren = [];
    function findBulletPoint(node) {
        if (node.id === bulletPoint.id) {
            bulletChildren = node.children || [];
            return;
        }
        if (node.children) {
            node.children.forEach(findBulletPoint);
        }
    }
    findBulletPoint(figmaData);

    if (bulletChildren.length > 0) {
        console.log(`   Number of bullet points: ${bulletChildren.length}`);

        // Calculate spacing between bullet points
        const spacings = [];
        for (let i = 0; i < bulletChildren.length - 1; i++) {
            const current = bulletChildren[i];
            const next = bulletChildren[i + 1];
            const spacing = next.y - (current.y + current.height);
            spacings.push(spacing);
            console.log(`   Point ${i + 1} to Point ${i + 2} spacing:`);
            console.log(`     = point${i + 2}.y - (point${i + 1}.y + point${i + 1}.height)`);
            console.log(`     = ${next.y} - (${current.y} + ${current.height}) = ${spacing}px`);
        }

        // Calculate bullet point container padding
        const bulletPaddingTop = bulletChildren[0].y;
        const bulletPaddingBottom = bulletPoint.height - (bulletChildren[bulletChildren.length - 1].y + bulletChildren[bulletChildren.length - 1].height);
        console.log(`   Bullet container padding:`);
        console.log(`     paddingTop = firstPoint.y = ${bulletPaddingTop}px`);
        console.log(`     paddingBottom = containerHeight - (lastPoint.y + lastPoint.height)`);
        console.log(`                   = ${bulletPoint.height} - (${bulletChildren[bulletChildren.length - 1].y} + ${bulletChildren[bulletChildren.length - 1].height}) = ${bulletPaddingBottom}px`);

        // Add spacing data for CSS
        const avgSpacing = spacings.length > 0 ? spacings.reduce((a, b) => a + b, 0) / spacings.length : 0;
        console.log(`   Average spacing: ${Math.round(avgSpacing)}px`);
    }

    console.log();
    console.log(`4. CSS IMPLEMENTATION VALUES:`);
    console.log(`   .pricing-card-${cardName.toLowerCase()} {`);
    console.log(`     padding: ${paddingTop}px ${paddingRight}px ${paddingBottom}px ${paddingLeft}px;`);
    console.log(`   }`);
    console.log(`   .text-block-to-features-margin: ${marginTextToBullet}px;`);
    console.log(`   .features-to-button-margin: ${marginBulletToButton}px;`);

    // Calculate bullet spacing again for CSS output
    if (bulletChildren.length > 0) {
        const bulletSpacings = [];
        for (let i = 0; i < bulletChildren.length - 1; i++) {
            const current = bulletChildren[i];
            const next = bulletChildren[i + 1];
            const spacing = next.y - (current.y + current.height);
            bulletSpacings.push(spacing);
        }
        const avgSpacing = bulletSpacings.length > 0 ? bulletSpacings.reduce((a, b) => a + b, 0) / bulletSpacings.length : 0;
        console.log(`   .bullet-point-spacing: ${Math.round(avgSpacing)}px;`);
    }

    console.log();
    console.log('='.repeat(80));
    console.log();
});

// PATTERN ANALYSIS
console.log('PATTERN ANALYSIS & RECOMMENDATIONS:');
console.log('-'.repeat(50));

const allPaddingData = cards.map((card, index) => {
    const textBlock = card.children.find(child => child.name.includes('Text-block'));
    const button = card.children.find(child => child.name.includes('Btn'));

    return {
        cardName: ['Free', 'Personal', 'Organization'][index],
        paddingTop: textBlock.y,
        paddingLeft: textBlock.x,
        paddingRight: card.width - (textBlock.x + textBlock.width),
        paddingBottom: card.height - (button.y + button.height)
    };
});

// Check for consistent patterns
const consistentLeft = allPaddingData.every(p => p.paddingLeft === allPaddingData[0].paddingLeft);
const consistentRight = allPaddingData.every(p => p.paddingRight === allPaddingData[0].paddingRight);

console.log(`Consistent horizontal padding: ${consistentLeft && consistentRight ? 'YES' : 'NO'}`);
if (consistentLeft && consistentRight) {
    console.log(`  All cards use: padding-left: ${allPaddingData[0].paddingLeft}px, padding-right: ${allPaddingData[0].paddingRight}px`);
}

console.log();
console.log(`Individual card variations:`);
allPaddingData.forEach(card => {
    console.log(`  ${card.cardName}: top=${card.paddingTop}px, bottom=${card.paddingBottom}px`);
});

console.log();
console.log('SPACING ISSUES IDENTIFIED:');
console.log('- Personal card has different vertical positioning (y=0 vs y=63.5)');
console.log('- Personal card is taller (761px vs 634px) indicating different content/spacing');
console.log('- Bullet point spacing varies between cards (check individual calculations above)');