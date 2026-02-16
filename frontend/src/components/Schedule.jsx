import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

function getParliamentSchedule() {
  const schedule = [];
  const today = new Date();
  
  // Canadian Parliament typically sits Mon-Fri
  // We'll calculate the next 8 weeks of sitting days
  
  for (let i = 0; i < 56; i++) {
    const date = new Date(today);
    date.setDate(today.getDate() + i);
    
    const dayOfWeek = date.getDay();
    const dateStr = date.toISOString().split('T')[0];
    
    // Parliament sits Monday-Friday (1-5)
    if (dayOfWeek >= 1 && dayOfWeek <= 5) {
      // Check if it's a Saturday processing day (add the Saturday AFTER this sitting day)
      const saturday = new Date(date);
      saturday.setDate(date.getDate() + (6 - dayOfWeek));
      
      if (saturday > today) {
        schedule.push({
          sittingDate: dateStr,
          processingDate: saturday.toISOString().split('T')[0],
          dayName: date.toLocaleDateString('en-CA', { weekday: 'long' }),
          sittingDateFormatted: date.toLocaleDateString('en-CA', { month: 'short', day: 'numeric' }),
          processingDateFormatted: saturday.toLocaleDateString('en-CA', { month: 'short', day: 'numeric' }),
        });
      }
    }
  }
  
  return schedule;
}

function Schedule() {
  const [schedule, setSchedule] = useState([]);
  
  useEffect(() => {
    setSchedule(getParliamentSchedule());
  }, []);
  
  const upcomingProcessing = schedule.filter(s => s.processingDate);
  const nextProcessingDate = upcomingProcessing.length > 0 ? upcomingProcessing[0].processingDate : null;
  
  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Parliament Schedule</h1>
        <p className="mt-2 text-gray-600">
          Scores are processed Saturday mornings based on the previous week's parliamentary activity.
        </p>
      </div>
      
      {nextProcessingDate && (
        <div className="bg-red-50 border-l-4 border-red-500 p-4 mb-8">
          <p className="text-red-700 font-medium">
            Next score processing: Saturday, {new Date(nextProcessingDate + 'T00:00:00').toLocaleDateString('en-CA', { month: 'long', day: 'numeric' })}
          </p>
        </div>
      )}
      
      <div className="bg-white shadow rounded-lg overflow-hidden">
        <div className="px-4 py-5 sm:px-6 bg-gray-50">
          <h2 className="text-lg font-medium text-gray-900">Upcoming Processing Dates</h2>
        </div>
        <ul className="divide-y divide-gray-200">
          {upcomingProcessing.slice(0, 12).map((item, idx) => (
            <li key={idx} className="px-4 py-4 sm:px-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-900">
                    Week of {item.sittingDateFormatted}
                  </p>
                  <p className="text-sm text-gray-500">
                    Sitting days: Mon-Fri
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-lg font-semibold text-red-600">
                    → {item.processingDateFormatted}
                  </p>
                  <p className="text-xs text-gray-400">Saturday AM</p>
                </div>
              </div>
            </li>
          ))}
        </ul>
      </div>
      
      <div className="mt-6 text-center text-sm text-gray-500">
        <p>Schedule is calculated based on standard Parliament sitting days (Monday-Friday).</p>
        <p className="mt-1">Actual processing may vary during parliamentary breaks.</p>
      </div>
    </div>
  );
}

export default Schedule;
