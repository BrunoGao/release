import dayjs from 'dayjs';
import utc from 'dayjs/plugin/utc';
import timezone from 'dayjs/plugin/timezone';
import { DateTimePattern } from '@/enum';

/**
 * format date time
 *
 * @param date date
 * @returns formatted date time
 */
export function formatDateTime(date?: dayjs.ConfigType) {
  return dayjs(date).format(DateTimePattern.DateTime);
}
dayjs.extend(utc);
dayjs.extend(timezone);
export function convertToBeijingTime(timestamp: dayjs.ConfigType) {
  return dayjs(timestamp).tz('Asia/Shanghai').format('YYYY-MM-DD HH:mm:ss');
}

export function formatDate(date: dayjs.ConfigType, format: string = 'YYYY-MM-DD') {
  return dayjs(date).format(format);
}

/**
 * format time
 *
 * @param time time
 * @param format format pattern, default is 'HH:mm:ss'
 * @returns formatted time
 */
export function formatTime(time: dayjs.ConfigType, format: string = 'HH:mm:ss') {
  return dayjs(time).format(format);
}
