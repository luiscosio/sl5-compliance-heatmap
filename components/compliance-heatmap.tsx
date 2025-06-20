"use client"

import type React from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { useState } from "react"

import complianceData from "@/data/compliance-data.json"

const companies = ["OpenAI", "Anthropic", "Google", "xAI", "Meta"]

interface ComplianceData {
  level: number
  description: string
  categories: Category[]
}

interface Category {
  name: string
  subcategories: Subcategory[]
}

interface Subcategory {
  name: string
  controls: Control[]
}

interface Control {
  name: string
  compliance: Record<string, ComplianceInfo>
}

interface ComplianceInfo {
  score: number
  sources: string[]
  justification: string
}

const getScoreColor = (score: number): string => {
  if (score === 0) return "bg-red-500"
  if (score === 100) return "bg-green-500"
  if (score >= 75) return "bg-green-400"
  if (score >= 50) return "bg-yellow-400"
  if (score >= 25) return "bg-orange-400"
  return "bg-red-400"
}

const getTextColor = (score: number): string => {
  return score >= 50 ? "text-white" : "text-white"
}

interface ComplianceCellProps {
  company: string
  control: Control
}

const ComplianceCell: React.FC<ComplianceCellProps> = ({ company, control }) => {
  const [isOpen, setIsOpen] = useState(false)
  const compliance = control.compliance[company]
  const score = compliance?.score || 0
  const justification = compliance?.justification || "No information available"
  const sources = compliance?.sources || []

  const handleClick = () => {
    setIsOpen(!isOpen)
  }

  return (
    <TooltipProvider>
      <Tooltip open={isOpen} onOpenChange={setIsOpen}>
        <TooltipTrigger asChild>
          <div
            onClick={handleClick}
            className={`
              w-16 h-12 flex items-center justify-center text-xs font-medium cursor-pointer
              transition-all duration-200 hover:scale-105 hover:shadow-md
              ${getScoreColor(score)} ${getTextColor(score)}
              border border-gray-200
              ${isOpen ? "ring-2 ring-blue-500" : ""}
            `}
          >
            {score}%
          </div>
        </TooltipTrigger>
        <TooltipContent side="top" className="max-w-sm p-3">
          <div className="space-y-2">
            <div className="font-semibold">
              {company} - {control.name}
            </div>
            <div className="text-sm">Score: {score}%</div>
            {justification && (
              <div className="text-sm">
                <span className="font-medium">Reason:</span> {justification}
              </div>
            )}
            {sources.length > 0 && (
              <div className="text-sm">
                <span className="font-medium">Sources:</span>
                <ul className="list-disc list-inside mt-1">
                  {sources.map((source, idx) => (
                    <li key={idx} className="text-xs">
                      {source}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}

export default function ComplianceHeatmap() {
  const data = complianceData as ComplianceData[]

  return (
    <div className="w-full max-w-7xl mx-auto p-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-2xl font-bold text-center">SL5 Compliance Heatmap</CardTitle>
          <p className="text-center text-muted-foreground">
            Track Security Level 5 (SL5) compliance of major AI labs. This data is compiled from public sources, is
            open-source, and updates daily using advanced Large Language Models to provide the latest insights into
            frontier model security.
          </p>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <div className="min-w-[800px]">
              {/* Header with company names */}
              <div className="flex mb-4">
                <div className="w-80 flex-shrink-0"></div>
                <div className="flex">
                  {companies.map((company) => (
                    <div
                      key={company}
                      className="w-16 h-12 flex items-center justify-center font-semibold text-sm bg-gray-100 border border-gray-200"
                    >
                      {company}
                    </div>
                  ))}
                </div>
              </div>

              {/* Scrollable content area */}
              <ScrollArea className="h-[600px] w-full">
                <div className="space-y-6">
                  {data.map((level) => (
                    <div key={level.level} className="space-y-4">
                      {/* Security Level Header */}
                      <div className="sticky top-0 bg-white z-10 pb-2">
                        <Badge variant="outline" className="text-lg px-4 py-2">
                          SL{level.level}
                        </Badge>
                        <p className="text-sm text-muted-foreground mt-1 max-w-4xl">{level.description}</p>
                        <Separator className="mt-2" />
                      </div>

                      {/* Categories and Controls */}
                      {level.categories.map((category, categoryIdx) => (
                        <div key={categoryIdx} className="space-y-3">
                          <h3 className="font-semibold text-base text-blue-700">{category.name}</h3>

                          {category.subcategories.map((subcategory, subcategoryIdx) => (
                            <div key={subcategoryIdx} className="space-y-2">
                              {subcategory.name && (
                                <h4 className="font-medium text-sm text-gray-600 ml-4">{subcategory.name}</h4>
                              )}

                              {subcategory.controls.map((control, controlIdx) => (
                                <div key={controlIdx} className="flex items-center">
                                  <div className="w-80 flex-shrink-0 pr-4">
                                    <div className="text-sm text-gray-700 ml-8">{control.name}</div>
                                  </div>
                                  <div className="flex">
                                    {companies.map((company) => (
                                      <ComplianceCell key={company} company={company} control={control} />
                                    ))}
                                  </div>
                                </div>
                              ))}
                            </div>
                          ))}
                        </div>
                      ))}
                    </div>
                  ))}
                </div>
              </ScrollArea>

              {/* Legend */}
              <div className="mt-6 flex items-center justify-center space-x-4 text-sm">
                <div className="flex items-center space-x-2">
                  <div className="w-4 h-4 bg-red-500 rounded"></div>
                  <span>0% Compliant</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-4 h-4 bg-orange-400 rounded"></div>
                  <span>25% Compliant</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-4 h-4 bg-yellow-400 rounded"></div>
                  <span>50% Compliant</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-4 h-4 bg-green-400 rounded"></div>
                  <span>75% Compliant</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-4 h-4 bg-green-500 rounded"></div>
                  <span>100% Compliant</span>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
