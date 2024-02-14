export const formatDate = (date: string) => {
  const dateObj = new Date(date);
  const options: Intl.DateTimeFormatOptions = {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  };
  const formattedDate = dateObj.toLocaleDateString(undefined, options);
  return formattedDate;
};
