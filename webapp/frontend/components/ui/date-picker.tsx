"use client"

import * as React from "react"
import { format, parseISO, isValid } from "date-fns"
import { CalendarIcon } from "lucide-react"

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Calendar } from "@/components/ui/calendar"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"

export interface DatePickerProps {
  value?: string
  onChange: (value: string) => void
  placeholder?: string
  id?: string
  className?: string
  disabled?: boolean
  yearPicker?: boolean
  fromYear?: number
  toYear?: number
}

/** Format for API: YYYY-MM-DD */
const API_FORMAT = "yyyy-MM-dd"
const DISPLAY_FORMAT = "MMM d, yyyy"

function parseValue(value: string | undefined): Date | undefined {
  if (!value?.trim()) return undefined
  try {
    const d = parseISO(value.trim())
    return isValid(d) ? d : undefined
  } catch {
    return undefined
  }
}

export function DatePicker({
  value,
  onChange,
  placeholder = "Pick a date",
  id,
  className,
  disabled,
  yearPicker = false,
  fromYear,
  toYear,
}: DatePickerProps) {
  const [open, setOpen] = React.useState(false)
  const date = parseValue(value)
  const currentYear = new Date().getFullYear()

  const handleSelect = (d: Date | undefined) => {
    if (!d) return
    onChange(format(d, API_FORMAT))
    setOpen(false)
  }

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          id={id}
          variant="outline"
          disabled={disabled}
          className={cn(
            "w-full justify-start text-left font-normal h-9 rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
            !date && "text-muted-foreground",
            className
          )}
        >
          <CalendarIcon className="mr-2 h-4 w-4 text-muted-foreground" />
          {date ? format(date, DISPLAY_FORMAT) : placeholder}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-auto p-0" align="start">
        <Calendar
          mode="single"
          selected={date}
          onSelect={handleSelect}
          defaultMonth={date}
          captionLayout={yearPicker ? "dropdown" : "label"}
          fromYear={yearPicker ? (fromYear ?? 1900) : undefined}
          toYear={yearPicker ? (toYear ?? currentYear) : undefined}
          initialFocus
        />
      </PopoverContent>
    </Popover>
  )
}
