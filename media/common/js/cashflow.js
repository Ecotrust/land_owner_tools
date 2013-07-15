var cashChart1;
var cashChart2;

var cashChartOptions = {
    stackSeries: true,
    seriesColors:['#D95F0E', '#EF3B2C','#415DAB', '#CB181D', '#FB6A4A', '#000000'],
    seriesDefaults:{
      renderer:$.jqplot.BarRenderer,
      useNegativeColors: false,
      rendererOptions: {
        fillToZero: true,
        highlightMouseOver: false,
        varyBarColor: true
      }
    },
    series:[
      {label:'Transportation Costs '},
      {label:'Cable Harvest Costs '},
      {label:'Timber Sale Income '},
      {label:'Ground Harvest Costs '},
      {label:'Helicopter Harvest Costs '},
      {
        label:'Net Revenue ',
        renderer:$.jqplot.LineRenderer,
        disableStack: true
      }
    ],
    highlighter : {
      show : true,
      showMarker: false,
      tooltip: true,
      useAxesFormatters: true,
      tooltipAxes: 'y',
      bringSeriesToFront: false
    },
    axes: {
      xaxis: {
        renderer: $.jqplot.CategoryAxisRenderer
        //ticks: data['years']
      },
      yaxis: {
        autoscale:true,
        tickOptions: {formatString: "$%'d"}
      }
    },
    legend: {
      renderer: $.jqplot.EnhancedLegendRenderer,
      rendererOptions: {
        // numberRows: 2
        numberColumns: 3
      },
      show: true,
      location: 'n',
      placement: 'outside'
    }
};

var refreshCashflow = function(refresh1, refresh2) {
  var opt1 = $('#cash-select-scenario1').find(":selected").val();
  var opt2 = $('#cash-select-scenario2').find(":selected").val();

  if (refresh1) {
    var cashflow_url1 = "/features/scenario/links/scenario-cash-flow/trees_scenario_" + opt1 +"/";

    if (opt1) {
      if (cashChart1) {
        $('#cash-chart1').html('');
        cashChart1.destroy();
      }
      $('#loading-cash-chart1').show();

      var xhr = $.get( cashflow_url1, function(data) {
          cashChartOptions.axes.xaxis.ticks = data['years'];
          var dataSeries = [
             data['haul'],
             data['cable'],
             data['gross'],
             data['ground'],
             data['heli'],
             data['net']
          ];

          cashChart1 = $.jqplot('cash-chart1', dataSeries,
            cashChartOptions
          );
          $('#loading-cash-chart1').hide();
      }, 'json');
    }
  }

  if (opt1 === opt2) {
    $('#cash2').hide();
    $('#cash-chart2').html('');
    cashChart2.destroy();
  } else {
    $('#cash2').show();
  }

  if (refresh2 && (opt1 !== opt2)) {
    var cashflow_url2 = "/features/scenario/links/scenario-cash-flow/trees_scenario_" + opt2 +"/";

    if (opt2) {
      if (cashChart2) {
        $('#cash-chart2').html('');
        cashChart2.destroy();
      }
      $('#loading-cash-chart2').show();

      $.get( cashflow_url2, function(data) {
          cashChartOptions.axes.xaxis.ticks = data['years'];
          var dataSeries = [
             data['haul'],
             data['cable'],
             data['gross'],
             data['ground'],
             data['heli'],
             data['net']
          ];

          cashChart2 = $.jqplot('cash-chart2', dataSeries,
            cashChartOptions
            // $.extend({}, cashChartOptions, {legend: {show: false}})
          );
          $('#loading-cash-chart2').hide();
      }, 'json');
    }
  }
};

$(document).ready(function() {
    $("#scenario-cash-tab").on('shown', function() {refreshCashflow(true, true);});
    $("#cash-select-scenario1").change(function() {refreshCashflow(true, false);});
    $("#cash-select-scenario2").change(function() {refreshCashflow(false, true);});
});
