var LEFT_BAR_SIZE = 150;
var WIDTH = 900;
var HEIGHT = 700;
var LABEL_WIDTH = 200;
var LIST_Y = 50;

var studySelection = d3.map();
var studySizes = d3.map();
var histogramBuckets = [
    {countByStudy: d3.map(), count: 0, min: 1, max: 1},
    {countByStudy: d3.map(), count: 0, min: 2, max: 2},
    {countByStudy: d3.map(), count: 0, min: 3, max: 3},
    {countByStudy: d3.map(), count: 0, min: 4, max: 4},
    {countByStudy: d3.map(), count: 0, min: 5, max: 5},
    {countByStudy: d3.map(), count: 0, min: 6, max: null}
];
var aggregationMethod = 'sum';
var sourceData;


function updateBuckets() {
    histogramBuckets.forEach(function(bucket) {
        bucket.count = 0;
        bucket.countByStudy = d3.map();
    });

    var byParticipant = d3.map();
    sourceData.entries().forEach(function(studyItem) {
        var studyName = studyItem.key;
        var studyValues = studyItem.value;

        if (!studySelection.get(studyName)) {
            return;
        }

        studyValues.entries().forEach(function(studyItem) {
            var participantID = studyItem.key;
            var count = studyItem.value;

            if (!byParticipant.has(participantID)) {
                byParticipant.set(participantID, {count: 0, studies: []});
            }

            var info = byParticipant.get(participantID);

            if (aggregationMethod === 'sum') {
                info.count += count;
                info.studies.push(studyName);
            } else {
                info.count = d3.max([count, info.count]);
                info.studies = [studyName];
            }
        });
    });
    
    byParticipant.values().forEach(function (info) {
        var count = info.count;
        var studies = info.studies;
        histogramBuckets.forEach(function (bucket) {
            var matchesMin = bucket.min == null || bucket.min <= count;
            var matchesMax = bucket.max == null || bucket.max >= count;
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


function updateViz() {
    var studyYCoord = d3.map();
    var studiesList = studySizes.entries().filter(function(entry) {
        return studySelection.get(entry.key);
    });

    studiesList.sort(function(a, b) {
        return b.value - a.value;
    });

    // Create left scales
    var leftPlacementScale = d3.scale.linear()
        .domain([0, studiesList.length])
        .range([0, HEIGHT - LIST_Y]);

    var maxStudyValue = d3.max(studiesList.map(function(x) {
        return x.value;
    }));
    var leftBarScale = d3.scale.linear()
        .domain([0, maxStudyValue])
        .range([0, LABEL_WIDTH]);

    // Create left list
    var leftList = d3.select('#left-list').selectAll('.left-entry')
        .data(studiesList, function(x) { return x.key; });

    var newItems = leftList.enter().append('g').classed('left-entry', true);
    newItems.append('rect').classed('item-rect', true);
    newItems.append('rect').classed('highlight-bar', true);
    newItems.append('text').classed('item-label', true);
    newItems.append('text').classed('item-count', true);
    newItems.append('rect').classed('item-bg', true);
    newItems.append('path')
        .classed('item-sep', true)
        .attr('d', 'M ' + (-LABEL_WIDTH) + ' 2 L 0 2')
        .style("stroke-dasharray", ('2', '1'));

    leftList.attr('transform', function(studyInfo, i) {
        studyYCoord.set(studyInfo.key, leftPlacementScale(i));
        return 'translate(0, ' + leftPlacementScale(i) + ')';
    });

    leftList.selectAll('.item-label')
        .attr('x' -2)
        .attr('y', -2)
        .text(function(studyInfo) {
            return studyInfo.key;
        });

    leftList.selectAll('.item-count')
        .text(function(studyInfo) {
            return studyInfo.value + ' participants';
        })
        .attr('x', -LABEL_WIDTH)
        .attr('y', -2);

    leftList.selectAll('.item-rect')
        .transition()
        .attr('x', function(studyInfo) {
            return -leftBarScale(studyInfo.value);
        })
        .attr('y', -15)
        .attr('height', 17)
        .attr('width', function(studyInfo) {
            return leftBarScale(studyInfo.value);
        });

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
    var rightPlacementScale = d3.scale.linear()
        .domain([0, histogramBuckets.length])
        .range([0, HEIGHT - LIST_Y]);

    var maxBucketValue = d3.max(histogramBuckets.map(function(x) {
        return x.count;
    }));
    var rightBarScale = d3.scale.linear()
        .domain([0, maxBucketValue])
        .range([0, LABEL_WIDTH]);

    // Create right list
    var rightList = d3.select('#right-list').selectAll('.right-entry')
        .data(histogramBuckets);

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

    rightList.attr('transform', function(bucket, i) {
        return 'translate(0, ' + rightPlacementScale(i) + ')';
    });

    rightList.selectAll('.item-label')
        .attr('x', 2)
        .text(function(bucket) {
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
        .text(function(bucket) {
            return bucket.count + ' participants';
        })
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
        .attr('width', function(bucket) {
            return rightBarScale(bucket.count);
        });

    rightList.selectAll('.highlight-bar')
        .attr('y', -15)
        .attr('height', 17)
        .attr('x', 0)
        .attr('width', 0);

    rightList.exit().remove();

    // Create chord scales
    var byStudyMax = d3.max(histogramBuckets.map(function(bucket) {
        return d3.max(bucket.countByStudy.values());
    }));
    var chordScale = d3.scale.linear()
        .domain([0, byStudyMax])
        .range([0, 17]);

    // Create chords
    var keySet = [];
    histogramBuckets.forEach(function(bucket, i) {
        bucket.countByStudy.keys().forEach(function(studyName) {
            keySet.push({study: studyName, bucket: i})
        });
    });

    var chords = d3.select('#chord-area').selectAll('.set-chord').data(keySet);

    chords.enter().append('path').classed('set-chord', true);

    chords.attr('opacity', 0.2)
        .attr('stroke-width', function (keySet) {
            var intersection = histogramBuckets[keySet.bucket].countByStudy
                .get(keySet.study);

            return chordScale(intersection);
        })
        .attr('d', function(keySet) {
            var startX = 0;
            var startY = studyYCoord.get(keySet.study) - 5;
            var endX = WIDTH - LABEL_WIDTH * 2;
            var endY = rightPlacementScale(keySet.bucket) - 5;

            var path = 'M ' + startX + ' ' + startY + ' ';
            path += 'C ' + (startX + 200) + ' ' + startY + ' ';
            path += (endX - 200) + ' ' + endY + ' ';
            path += endX + ' ' + endY;
            return path;
        });

    chords.exit().remove();

    // Attach listeners
    rightList.on('mouseenter', function(bucket, i) {
        d3.select(this).classed('active', true);
        
        var filteredChords = chords.filter(function(keySet) {
            return keySet.bucket == i;
        });

        var counts = bucket.countByStudy;

        leftList.selectAll('.highlight-bar').transition()
            .attr('x', function(studyInfo) {
                if (counts.has(studyInfo.key)) {
                    return -leftBarScale(counts.get(studyInfo.key));
                } else {
                    return 0;
                }
            })
            .attr('width', function(studyInfo) {
                if (counts.has(studyInfo.key)) {
                    return leftBarScale(counts.get(studyInfo.key));
                } else {
                    return 0;
                }
            });

        leftList.selectAll('.item-count').text(function(studyInfo) {
            var count = counts.get(studyInfo.key);
            if (count === undefined) { count = 0; }
            return studyInfo.value + ' part. (' + count + ' high.)';
        });

        filteredChords.classed('active', true);
    });

    rightList.on('mouseleave', function(bucket, i) {
        d3.select('#viz-target').selectAll('.active').classed('active', false);

        leftList.selectAll('.highlight-bar')
            .transition()
            .attr('x', 0)
            .attr('width', 0);

        leftList.selectAll('.item-count').text(function(studyInfo) {
            return studyInfo.value + ' participants';
        });
    });

    leftList.on('mouseenter', function(studyInfo) {
        d3.select(this).classed('active', true);
        
        var filteredChords = chords.filter(function(keySet) {
            return keySet.study == studyInfo.key;
        });

        rightList.selectAll('.highlight-bar').transition()
            .attr('width', function(bucket) {
                var counts = bucket.countByStudy;
                if (counts.has(studyInfo.key)) {
                    return rightBarScale(counts.get(studyInfo.key));
                } else {
                    return 0;
                }
            });

        rightList.selectAll('.item-count')
            .text(function(bucket) {
                var counts = bucket.countByStudy;
                var highlighted = counts.get(studyInfo.key);

                if (highlighted === undefined) {
                    highlighted = 0;
                }
                
                var retStr = bucket.count + ' part. (';
                retStr += highlighted + ' high.)';

                return retStr;
            });

        filteredChords.classed('active', true);
    });

    leftList.on('mouseleave', function(studyInfo) {
        d3.select('#viz-target').selectAll('.active').classed('active', false);

        rightList.selectAll('.highlight-bar')
            .transition()
            .attr('x', 0)
            .attr('width', 0);

        rightList.selectAll('.item-count').text(function(bucket) {
            return bucket.count + ' participants';
        })
    });
}


function initViz(err, data) {
    // Process data
    sourceData = d3.map(data);
    sourceData.keys().forEach(function(studyName) {
        var studyInfo = d3.map(sourceData.get(studyName));
        
        sourceData.set(studyName, studyInfo);
        studySelection.set(studyName, true);

        studySizes.set(studyName, studyInfo.values().length);
    });

    // Create chart frame
    var vizTarget = d3.select('#viz-target');
    
    var leftFrameGroup = vizTarget.append('g').attr('id', 'left-frame-group');
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

    var rightFrameGroup = vizTarget.append('g').attr('id', 'right-frame-group');
    var rightFrameStartX = WIDTH - LABEL_WIDTH;
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


function createStudySelectionList() {
    var list = d3.select('#study-selection-list').selectAll('.study-check')
        .data(studySelection.keys());

    var newItems = list.enter().append('div')
        .classed('control-group', true)
        .classed('study-check', true);

    var newInnerItem = newItems.append('label')
        .classed('study-check', true)
        .classed('checkbox', true);

    newInnerItem.append('input')
        .attr('type', 'checkbox')
        .classed('study-input-check', true)
        .property('checked', function(studyName) {
            return studySelection.get(studyName);
        });
    
    newInnerItem.append('span').html(function(studyName) {
        return studyName
    });
}


function updateBucketTable() {
    var listItems = d3.select('#bucket-list-bod').selectAll('.bucket-list-item')
        .data(histogramBuckets.map(function (x, i) { return i; }));

    var newListItems = listItems.enter().append('tr')
        .classed('bucket-list-item', true);

    newListItems.append('td').append('input').classed('min-input', true);
    newListItems.append('td').append('input').classed('max-input', true);
    newListItems.append('td').append('a')
        .attr('href', '#')
        .html('delete bucket')
        .classed('del-link', true);

    listItems.selectAll('.min-input')
        .attr('value', function(i) {
            var info = histogramBuckets[i];
            var val = info.min === null ? '' : info.min;
            return val;
        });

    listItems.selectAll('.max-input')
        .attr('value', function(i) {
            var info = histogramBuckets[i];
            var val = info.max === null ? '' : info.max;
            return val;
        });

    listItems.selectAll('.del-link').on('click', function(i) {
        histogramBuckets.splice(i, 1);
        updateBucketTable();
        d3.event.preventDefault();
    });

    listItems.exit().remove();
}


$('#aggregation-drop').change(function() {
    aggregationMethod = $('#aggregation-drop option:selected').val();
    updateBuckets();
    updateViz();
});


$('#change-studies-link').click(function() {
    $('#main-body').slideUp();
    $('#study-selector').slideDown();
    return false;
});


$('#finish-change-studies-link').click(function() {
    var checks = d3.select('#study-selection-list').selectAll('.study-check');

    checks.each(function(studyName) {
        var checked = d3.select(this).select('.study-input-check')
            .property('checked');

        studySelection.set(studyName, checked);
    });

    updateBuckets();
    updateViz();

    $('#main-body').slideDown();
    $('#study-selector').slideUp();
    return false;
});


$('#add-bucket-link').click(function() {
    histogramBuckets.push({
        countByStudy: d3.map(),
        count: 0,
        min: null,
        max: null
    });

    updateBucketTable();
    return false;
});


$('#change-histograms-link').click(function() {
    $('#main-body').slideUp();
    $('#bucket-selector').slideDown();
    return false;
})


$('#finish-buckets-link').click(function() {
    var items = d3.select('#bucket-list-bod').selectAll('.bucket-list-item');
    items.each(function(i) {
        var minInput = d3.select(this).select('.min-input');
        var newMin = parseInt(minInput.node().value, 10);

        if (isNaN(newMin)) {
            newMin = null;
        }

        histogramBuckets[i].min = newMin;

        var maxInput = d3.select(this).select('.max-input');
        var newMax = parseInt(maxInput.node().value, 10);

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


d3.json('/base/access_data/distribution', initViz);
