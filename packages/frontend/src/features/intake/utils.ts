export function filterOptions(options: string[], query: string) {
  const cleanQuery = query.trim().toLowerCase()
  if (!cleanQuery) return options
  return options.filter((option) => option.toLowerCase().includes(cleanQuery))
}
