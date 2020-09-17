/**
 * Client-side logic for displaying a frequency distribution of CDIs / study.
 *
 * Copyright (C) 2014 A. Samuel Pottinger ("Sam Pottinger", gleap.org)
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
**/

// Thanks https://stackoverflow.com/questions/36644438/how-to-convert-a-plain-object-into-an-es6-map
Object.entries = typeof Object.entries === 'function' ? Object.entries : obj => Object.keys(obj).map(k => [k, obj[k]]);

let LEFT_BAR_SIZE = 150;
let WIDTH = 900;
let HEIGHT = 700;
let LABEL_WIDTH = 200;
let LIST_Y = 50;

let studySelection = new Map();
let studySizes = new Map();

let histogramBuckets = [
    {countByStudy: new Map(), count: 0, min: 1, max: 1},
    {countByStudy: new Map(), count: 0, min: 2, max: 2},
    {countByStudy: new Map(), count: 0, min: 3, max: 3},
    {countByStudy: new Map(), count: 0, min: 4, max: 4},
    {countByStudy: new Map(), count: 0, min: 5, max: 5},
    {countByStudy: new Map(), count: 0, min: 6, max: 6},
    {countByStudy: new Map(), count: 0, min: 7, max: 7},
    {countByStudy: new Map(), count: 0, min: 8, max: 8},
    {countByStudy: new Map(), count: 0, min: 9, max: 9},
    {countByStudy: new Map(), count: 0, min: 10, max: 10},
    {countByStudy: new Map(), count: 0, min: 11, max: 11},
    {countByStudy: new Map(), count: 0, min: 12, max: null}
];

let aggregationMethod = 'sum';
let sourceData;


/**
 * For compatibility, emulate old d3 map keys.
 */
function iterateKeys(targetMap) {
    return Array.from(targetMap.entries()).map((x) => x[0]);
}


/**
 * For compatibility, emulate old d3 map values.
 */
function iterateValues(targetMap) {
    return Array.from(targetMap.entries()).map((x) => x[1]);
}


/**
 * For compatibility, emulate old d3 map values.
 */
function iterateEntries(targetMap) {
    return Array.from(targetMap.entries()).map(
        (x) => { return {"key": x[0], "value": x[1]}; }
    );
}


/**
 * Update the frequency distribution buckets.
 *
 * Recalculate the distribution of CDIs per study for the frequency distribution
 * display.
 */
function updateBuckets() {
    histogramBuckets.forEach(function(bucket) {
        bucket.count = 0;
        bucket.countByStudy = new Map();
    });

    let byParticipant = new Map();
    iterateEntries(sourceData).forEach(function(studyItem) {
        let studyName = studyItem.key;
        let studyValues = studyItem.value;

        if (!studySelection.get(studyName)) {
            return;
        }

        iterateEntries(studyValues).forEach(function(studyItem) {
            let participantID = studyItem.key;
            let count = studyItem.value;

            if (!byParticipant.has(participantID)) {
                byParticipant.set(participantID, {count: 0, studies: []});
            }

            let info = byParticipant.get(participantID);

            if (aggregationMethod === 'sum') {
                info.count += count;
                info.studies.push(studyName);
            } else {
                info.count = d3.max([count, info.count]);
                info.studies = [studyName];
            }
        });
    });

    iterateValues(byParticipant).forEach(function (info) {
        let count = info.count;
        let studies = info.studies;
        histogramBuckets.forEach(function (bucket) {
            let matchesMin = bucket.min == null || bucket.min <= count;
            let matchesMax = bucket.max == null || bucket.max >= count;
            if (matchesMin && matchesMax) {
                bucket.count += 1;

                studies.forEach(function (study) {
                    if (!bucket.countByStudy.has(study)) {
                        bucket.countByStudy.set(study, 0);
                    }
                    bucket.countByStudy.set(
                        study,
                        bucket.countByStudy.get(study) + 1
                    );
                });
            }
        });
    });
}


/**
 * Redraw the frequency distribution visualization.
 *
 * Redraw a simple frequency distrubtion display that shows how many CDIs were
 * collected per study with the studies on the left side and the frequency
 * "buckets" on the right side.
 */
function updateViz() {
    let studyYCoord = new Map();
    let studiesList = iterateEntries(studySizes).filter(
        (entry) => studySelection.get(entry.key)
    );

    studiesList.sort((a, b) => b.value - a.value);

    // Create left scales
    let leftPlacementScale = d3.scaleLinear()
        .domain([0, studiesList.length])
        .range([0, HEIGHT - LIST_Y]);

    let maxStudyValue = d3.max(studiesList.map((x) => x.value));
    let leftBarScale = d3.scaleLinear()
        .domain([0, maxStudyValue])
        .range([0, LABEL_WIDTH]);

    // Create left list
    let leftList = d3.select('#left-list').selectAll('.left-entry')
        .data(studiesList, (x) => x.key);

    let newItems = leftList.enter().append('g').classed('left-entry', true);
    newItems.append('rect').classed('item-rect', true);
    newItems.append('rect').classed('highlight-bar', true);
    newItems.append('text').classed('item-label', true);
    newItems.append('text').classed('item-count', true);
    newItems.append('rect').classed('item-bg', true);
    newItems.append('path')
        .classed('item-sep', true)
        .attr('d', 'M ' + (-LABEL_WIDTH) + ' 2 L 0 2')
        .style("stroke-dasharray", ('2', '1'));

    leftList = d3.select('#left-list').selectAll('.left-entry');

    leftList.attr('transform', (studyInfo, i) => {
        studyYCoord.set(studyInfo.key, leftPlacementScale(i));
        return 'translate(0, ' + leftPlacementScale(i) + ')';
    });

    leftList.selectAll('.item-label')
        .attr('x', -2)
        .attr('y', -2)
        .text((studyInfo) => studyInfo.key);

    leftList.selectAll('.item-count')
        .text((studyInfo) => studyInfo.value + ' participants')
        .attr('x', -LABEL_WIDTH)
        .attr('y', -2);

    leftList.selectAll('.item-rect')
        .transition()
        .attr('x', function(studyInfo) {
            return -leftBarScale(studyInfo.value);
        })
        .attr('y', -15)
        .attr('height', 17)
        .attr('width', (studyInfo) => leftBarScale(studyInfo.value));

    leftList.selectAll('.highlight-bar')
        .attr('y', -15)
        .attr('height', 17)
        .attr('x', 0)
        .attr('width', 0);

    leftList.selectAll('.item-bg')
        .attr('x', -LABEL_WIDTH)
        .attr('y', -15)
        .attr('width', LABEL_WIDTH)
        .attr('height', 17);

    leftList.exit().remove();

    // Create right scales
    let rightPlacementScale = d3.scaleLinear()
        .domain([0, histogramBuckets.length])
        .range([0, HEIGHT - LIST_Y]);

    let maxBucketValue = d3.max(histogramBuckets.map((x) => x.count));
    let rightBarScale = d3.scaleLinear()
        .domain([0, maxBucketValue])
        .range([0, LABEL_WIDTH]);

    // Create right list
    let rightList = d3.select('#right-list').selectAll('.right-entry')
        .data(histogramBuckets);

    rightList.exit().remove();

    newItems = rightList.enter().append('g').classed('right-entry', true);
    newItems.append('rect').classed('item-rect', true);
    newItems.append('rect').classed('highlight-bar', true);
    newItems.append('text').classed('item-label', true);
    newItems.append('text').classed('item-count', true);
    newItems.append('path')
        .classed('item-sep', true)
        .attr('d', 'M 0 2 L ' + LABEL_WIDTH + ' 2')
        .style('stroke-dasharray', ('2', '1'));
    newItems.append('rect').classed('item-bg', true);

    rightList = d3.select('#right-list').selectAll('.right-entry');

    rightList.attr(
      'transform',
      (bucket, i) => 'translate(0, ' + rightPlacementScale(i) + ')'
    );

    rightList.selectAll('.item-label')
        .attr('x', 2)
        .text((bucket) => {
            if (bucket.min === null) {
                return '<= ' + bucket.max + ' CDIs';
            } else if (bucket.max === null) {
                return '>= ' + bucket.min + ' CDIs';
            } else {
                if (bucket.min == bucket.max) {
                    return bucket.min + ' CDIs';
                } else {
                    return bucket.min + ' - ' + bucket.max + ' CDIs';
                }
            }
        });

    rightList.selectAll('.item-count')
        .text((bucket) => bucket.count + ' participants')
        .attr('x', LABEL_WIDTH)
        .attr('y', -2);

    rightList.selectAll('.item-bg')
        .attr('x', 0)
        .attr('y', -15)
        .attr('width', LABEL_WIDTH)
        .attr('height', 17);

    rightList.selectAll('.item-rect')
        .transition()
        .attr('x', 0)
        .attr('y', -15)
        .attr('height', 17)
        .attr('width', (bucket) => rightBarScale(bucket.count));

    rightList.selectAll('.highlight-bar')
        .attr('y', -15)
        .attr('height', 17)
        .attr('x', 0)
        .attr('width', 0);

    // Create chord scales
    let byStudyMax = d3.max(histogramBuckets.map((bucket) => {
        return d3.max(iterateValues(bucket.countByStudy));
    }));
    let chordScale = d3.scaleLinear()
        .domain([0, byStudyMax])
        .range([0, 17]);

    // Create chords
    let keySet = [];
    histogramBuckets.forEach((bucket, i) => {
        iterateKeys(bucket.countByStudy).forEach((studyName) => {
            keySet.push({study: studyName, bucket: i})
        });
    });

    let chords = d3.select('#chord-area').selectAll('.set-chord').data(keySet);

    chords.exit().remove();

    chords.enter().append('path').classed('set-chord', true);

    chords = d3.select('#chord-area').selectAll('.set-chord');

    chords.attr('opacity', 0.2)
        .attr('stroke-width', (keySet) => {
            let intersection = histogramBuckets[keySet.bucket].countByStudy
                .get(keySet.study);

            return chordScale(intersection);
        })
        .attr('d', (keySet) => {
            let startX = 0;
            let startY = studyYCoord.get(keySet.study) - 5;
            let endX = WIDTH - LABEL_WIDTH * 2;
            let endY = rightPlacementScale(keySet.bucket) - 5;

            let path = 'M ' + startX + ' ' + startY + ' ';
            path += 'C ' + (startX + 200) + ' ' + startY + ' ';
            path += (endX - 200) + ' ' + endY + ' ';
            path += endX + ' ' + endY;
            return path;
        });

    chords = d3.select('#chord-area').selectAll('.set-chord');

    // Attach listeners
    rightList.on('mouseenter', function(event, bucket) {
        d3.select(this).classed('active', true);

        let i = rightList.nodes().indexOf(this);

        let filteredChords = chords.filter((keySet) => {
            return keySet.bucket == i;
        });

        let counts = bucket.countByStudy;

        leftList.selectAll('.highlight-bar').transition()
            .attr('x', (studyInfo) => {
                if (counts.has(studyInfo.key)) {
                    return -leftBarScale(counts.get(studyInfo.key));
                } else {
                    return 0;
                }
            })
            .attr('width', (studyInfo) => {
                if (counts.has(studyInfo.key)) {
                    return leftBarScale(counts.get(studyInfo.key));
                } else {
                    return 0;
                }
            });

        leftList.selectAll('.item-count').text((studyInfo) => {
            let count = counts.get(studyInfo.key);
            if (count === undefined) { count = 0; }
            return studyInfo.value + ' part. (' + count + ' high.)';
        });

        filteredChords.classed('active', true);
    });

    rightList.on('mouseleave', function(event, bucket) {
        d3.select('#viz-target').selectAll('.active').classed('active', false);

        leftList.selectAll('.highlight-bar')
            .transition()
            .attr('x', 0)
            .attr('width', 0);

        leftList.selectAll('.item-count').text(function(studyInfo) {
            return studyInfo.value + ' participants';
        });
    });

    leftList.on('mouseenter', function(event, studyInfo) {
        d3.select(this).classed('active', true);

        let filteredChords = chords.filter(function(keySet) {
            return keySet.study == studyInfo.key;
        });

        rightList.selectAll('.highlight-bar').transition()
            .attr('width', (bucket) => {
                let counts = bucket.countByStudy;
                if (counts.has(studyInfo.key)) {
                    return rightBarScale(counts.get(studyInfo.key));
                } else {
                    return 0;
                }
            });

        rightList.selectAll('.item-count')
            .text((bucket) => {
                let counts = bucket.countByStudy;
                let highlighted = counts.get(studyInfo.key);

                if (highlighted === undefined) {
                    highlighted = 0;
                }

                let retStr = bucket.count + ' part. (';
                retStr += highlighted + ' high.)';

                return retStr;
            });

        filteredChords.classed('active', true);
    });

    leftList.on('mouseleave', function(event, studyInfo) {
        d3.select('#viz-target').selectAll('.active').classed('active', false);

        rightList.selectAll('.highlight-bar')
            .transition()
            .attr('x', 0)
            .attr('width', 0);

        rightList.selectAll('.item-count').text((bucket) => {
            return bucket.count + ' participants';
        })
    });
}


/**
 * Process and display the frequency distribution data returned by the server.
 */
function initViz(data) {
    // Process data
    sourceData = new Map(Object.entries(data));
    iterateKeys(sourceData).forEach((studyName) => {
        let studyInfo = new Map(Object.entries(sourceData.get(studyName)));

        sourceData.set(studyName, studyInfo);
        studySelection.set(studyName, true);

        studySizes.set(studyName, iterateValues(studyInfo).length);
    });

    // Create chart frame
    let vizTarget = d3.select('#viz-target');

    let leftFrameGroup = vizTarget.append('g').attr('id', 'left-frame-group');
    leftFrameGroup.attr('transform', 'translate(' + LABEL_WIDTH + ',0)');
    leftFrameGroup.append('text')
        .classed('frame-elem', true)
        .attr('x', '0')
        .attr('y', 14)
        .text('Studies');

    leftFrameGroup.append('rect')
        .classed('frame-elem', true)
        .attr('x', -LABEL_WIDTH)
        .attr('y', 16)
        .attr('width', LABEL_WIDTH)
        .attr('height', 1);

    let rightFrameGroup = vizTarget.append('g').attr('id', 'right-frame-group');
    let rightFrameStartX = WIDTH - LABEL_WIDTH;
    rightFrameGroup.attr('transform', 'translate(' + rightFrameStartX + ',0)');
    rightFrameGroup.append('text')
        .classed('frame-elem', true)
        .attr('x', 0)
        .attr('y', 14)
        .text('Num CDIs / participant');

    rightFrameGroup.append('rect')
        .classed('frame-elem', true)
        .attr('x', 0)
        .attr('y', 16)
        .attr('width', LABEL_WIDTH)
        .attr('height', 1);

    // Create chart contents
    vizTarget.append('g').attr('id', 'left-list')
        .attr('transform', 'translate(' + LABEL_WIDTH + ',' + LIST_Y + ')');

    vizTarget.append('g').attr('id', 'right-list')
        .attr(
            'transform',
            'translate(' + rightFrameStartX + ',' + LIST_Y + ')'
        );

    vizTarget.append('g').attr('id', 'chord-area')
        .attr('transform', 'translate(' + LABEL_WIDTH + ',' + LIST_Y + ')');

    updateBuckets();
    updateViz();
    createStudySelectionList();
    updateBucketTable();

    // Show controls
    $('#top-controls').delay(500).slideDown();
}


/**
 * Create the UI to select the studies to include in the frequency calc.
 *
 * Create a user interface that allows the client to include / exclude studies
 * within the frequency distribution calculation.
 */
function createStudySelectionList() {
    let list = d3.select('#study-selection-list').selectAll('.study-check')
        .data(studySelection.keys());

    let newItems = list.enter().append('div')
        .classed('control-group', true)
        .classed('study-check', true);

    let newInnerItem = newItems.append('label')
        .classed('study-check', true)
        .classed('checkbox', true);

    newInnerItem.append('input')
        .attr('type', 'checkbox')
        .classed('study-input-check', true)
        .property('checked', (studyName) => studySelection.get(studyName));

    newInnerItem.append('span').html((studyName) => studyName);
}


/**
 * Update the display that shows how many studies had how many CDIs.
 */
function updateBucketTable() {
    let listItems = d3.select('#bucket-list-bod').selectAll('.bucket-list-item')
        .data(histogramBuckets.map((x, i) => i));

    let newListItems = listItems.enter().append('tr')
        .classed('bucket-list-item', true);

    listItems.exit().remove();

    newListItems.append('td').append('input').classed('min-input', true);
    newListItems.append('td').append('input').classed('max-input', true);
    newListItems.append('td').append('a')
        .attr('href', '#')
        .html('delete bucket')
        .classed('del-link', true);

    listItems = d3.select('#bucket-list-bod').selectAll('.bucket-list-item')

    listItems.selectAll('.min-input')
        .attr('value', (i) => {
            let info = histogramBuckets[i];
            let val = info.min === null ? '' : info.min;
            return val;
        });

    listItems.selectAll('.max-input')
        .attr('value', (i) => {
            let info = histogramBuckets[i];
            let val = info.max === null ? '' : info.max;
            return val;
        });

    listItems.selectAll('.del-link').on('click', function(event, i) {
        histogramBuckets.splice(i, 1);
        updateBucketTable();
        event.preventDefault();
    });
}


/**
 * Register callback for when the user changes the frequency distribution
 * calculation method.
 */
$('#aggregation-drop').change(() => {
    aggregationMethod = $('#aggregation-drop option:selected').val();
    updateBuckets();
    updateViz();
});


/**
 * Register callback for when the user wants to change the studies that should
 * be included in the frequency distribution calcuation.
 */
$('#change-studies-link').click(() => {
    $('#main-body').slideUp();
    $('#study-selector').slideDown();
    return false;
});


/**
 * Register callback for when the user finishes selecting the studies that
 * should be included in the frequency distribution calcuation.
 */
$('#finish-change-studies-link').click(() => {
    let checks = d3.select('#study-selection-list').selectAll('.study-check');

    checks.each((studyName) => {
        let checked = d3.select(this).select('.study-input-check')
            .property('checked');

        studySelection.set(studyName, checked);
    });

    updateBuckets();
    updateViz();

    $('#main-body').slideDown();
    $('#study-selector').slideUp();
    return false;
});


/**
 * Register callback for when the user adds a new frequency distribution
 * classification. This allows the user to have the frequency distribution
 * group all of the studies with some number of CDIs together into the same
 * bucket to display the "long tail" of the distribution more effectively.
 */
$('#add-bucket-link').click(() => {
    histogramBuckets.push({
        countByStudy: new Map(),
        count: 0,
        min: null,
        max: null
    });

    updateBucketTable();
    return false;
});


/**
 * Register callback for when the user wants to change the histogram buckets.
 */
$('#change-histograms-link').click(() => {
    $('#main-body').slideUp();
    $('#bucket-selector').slideDown();
    return false;
})


/**
 * Register callback for when the user finishes changing the historgram buckets.
 */
$('#finish-buckets-link').click(() => {
    let items = d3.select('#bucket-list-bod').selectAll('.bucket-list-item');
    items.each(function(i) {
        let minInput = d3.select(this).select('.min-input');
        let newMin = parseInt(minInput.node().value, 10);

        if (isNaN(newMin)) {
            newMin = null;
        }

        histogramBuckets[i].min = newMin;

        let maxInput = d3.select(this).select('.max-input');
        let newMax = parseInt(maxInput.node().value, 10);

        if (isNaN(newMax)) {
            newMax = null;
        }

        histogramBuckets[i].max = newMax;
    });

    updateBuckets();
    updateViz();

    $('#main-body').slideDown();
    $('#bucket-selector').slideUp();
});


// Request frequency distribution data from the server.
d3.json('/base/access_data/distribution').then(initViz);
